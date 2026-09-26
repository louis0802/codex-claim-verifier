#!/usr/bin/env python3
"""Machine-readable bridge for the public Node CLI, using existing audit readers."""
import argparse
import json
import os
import stat
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from claim_verifier.config import codex_home, load
from claim_verifier.diagnostics import data_roots, latest_audit, read_ledgers
from claim_verifier.install_state import EXPECTED, SCHEMA, identity, initialize, read_state
from audit import render as render_audit


def doctor(installation: dict) -> dict:
    errors = []
    attention = []
    root = Path(installation["root"]) if installation.get("root") else None
    package = False
    capable = False
    current = None
    if installation.get("installed") and root:
        try:
            manifest = json.loads((root / ".codex-plugin/plugin.json").read_text())
            package = manifest.get("name") == "claim-verifier" and manifest.get("version") == installation.get("version")
            if not package:
                raise ValueError("Installed manifest does not match Codex listing")
            required = ["hooks/hooks.json", "hooks/claim_verifier.py", "scripts/audit.py", "scripts/doctor.py"]
            required += [f"claim_verifier/{name}.py" for name in
                         ("hook", "config", "store", "diagnostics", "collector", "claims", "verify", "semantic", "footer")]
            if any(not (root / file).is_file() or (root / file).is_symlink() for file in required):
                raise ValueError("Installed plugin runtime is incomplete. Run setup --upgrade.")
            current = identity(root)
            capable = (root / "claim_verifier/install_state.py").is_file()
            if capable and not (root / "hooks/run.mjs").is_file():
                raise ValueError("Installed hook launcher is missing. Run setup --upgrade.")
        except (OSError, ValueError, KeyError) as exc:
            errors.append(str(exc))
    else:
        errors.append("Claim Verifier is not installed. Run Claim Verifier setup from the GitHub release package.")
    if installation.get("enabled") is False:
        attention.append("Claim Verifier is disabled in Codex. Enable it in Codex plugin settings.")
    if package and not capable:
        attention.append("This installed plugin predates automatic setup detection. Run Claim Verifier setup --upgrade from the GitHub release package.")
    config_ok = False
    settings = {}
    try:
        config_path = codex_home() / "claim-verifier.toml"
        if not config_path.is_file() or config_path.is_symlink():
            raise ValueError("Global configuration is missing or symlinked. Run setup.")
        settings = load(str(codex_home()), include_project=False)
        model = settings["model"]
        if (type(model.get("enabled")) is not bool or type(model.get("only_for_ambiguous_claims")) is not bool or
                not isinstance(model.get("model"), str) or not model["model"].strip() or
                model.get("reasoning_effort") not in {"none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra"}):
            raise ValueError("Invalid claim_verifier.model settings")
        config_ok = True
        if not settings["enabled"] or settings["level"] == "off":
            attention.append("Verification is disabled in existing configuration; configuration was preserved.")
    except (OSError, ValueError, TypeError, KeyError) as exc:
        errors.append(f"Configuration: {exc}")
    state = {}
    try:
        state = read_state()
    except (OSError, ValueError) as exc:
        errors.append(f"Installation state: {exc}")
    roots = data_roots()
    storage_ok = any(path.is_dir() and not path.is_symlink() and
                     stat.S_IMODE(path.stat().st_mode) == 0o700 and os.access(path, os.R_OK | os.W_OK | os.X_OK)
                     for path in roots)
    if not storage_ok:
        errors.append("Private audit storage is missing or inaccessible. Run setup.")
    current_activity = bool(current and state.get("identity") == current)
    seen = state.get("hooks_seen", []) if current_activity else []
    states = read_ledgers()
    audit_ok = bool(current_activity and state.get("audit_created") and any(
        ledger.get("session_id") == state.get("audit_session_id") and ledger.get("audits") and
        ledger.get("runtime", {}).get("package_identity") == current
        for ledger in states))
    hooks_ok = capable and all(hook in seen for hook in EXPECTED)
    ready = bool(package and config_ok and storage_ok and hooks_ok and audit_ok and not errors and not attention)
    status = ("READY" if ready else "BROKEN INSTALLATION" if errors else "ATTENTION REQUIRED" if attention
              else "WAITING FOR AUDIT" if hooks_ok else "WAITING FOR HOOK REVIEW")
    return {"status": status, "exit_code": 0 if ready else 2 if errors else 1,
            "installation": package, "configuration": config_ok, "audit_storage": storage_ok,
            "hook_activity": "OBSERVED" if current_activity and seen else "NOT_OBSERVED",
            "hooks_seen": seen, "hooks_observed": hooks_ok, "audit_generation": audit_ok, "hook_trust": "UNKNOWN",
            "version": installation.get("version"), "config_schema": SCHEMA,
            "errors": errors, "attention": attention}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["doctor", "initialize", "audit-latest", "audit-list"])
    parser.add_argument("--installation", default="{}")
    parser.add_argument("--data-root")
    args = parser.parse_args()
    installation = json.loads(args.installation)
    if args.command == "initialize":
        result = initialize(Path(installation["root"]), installation["version"], Path(args.data_root),
                            installation.get("selector", "claim-verifier@personal"))
    elif args.command == "doctor":
        result = doctor(installation)
    elif args.command == "audit-latest":
        audit = latest_audit()
        result = {"text": render_audit(audit), "audit": audit}
    else:
        audits = [{"session": state["session_id"][:12], "timestamp": audit.get("timestamp"),
                   "result": audit.get("result")} for state in read_ledgers() for audit in state.get("audits", [])]
        result = {"audits": sorted(audits, key=lambda item: item.get("timestamp") or "", reverse=True)}
    print(json.dumps(result))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"error": str(exc)}))
        sys.exit(2)
