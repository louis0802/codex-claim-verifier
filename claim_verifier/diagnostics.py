"""Small, non-sensitive hook diagnostics and read-only ledger summaries."""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from .collector import redact
from .config import codex_home, load

HOOKS = {"prompt": "UserPromptSubmit", "tool": "PostToolUse", "stop": "Stop"}
SMOKE_MARKER = "CLAIM-VERIFIER-DESKTOP-SMOKE"
MISSING_SESSION = "__claim_verifier_missing_session__"
HEARTBEAT_LIMIT = 60
RECEIPT_VISIBILITY = ("NATIVE_VISIBLE", "SYSTEM_MESSAGE_VISIBLE", "AUDIT_ONLY", "NOT_SUPPORTED", "INCONCLUSIVE")
DESKTOP_OBSERVATIONS_FILE = "desktop-observations.json"


def _safe_text(value: object, limit: int = 128) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"[\x00-\x1f\x7f]", "?", value)[:limit]


def _safe_cwd(value: object) -> str:
    raw = _safe_text(value, 300)
    home = str(Path.home())
    if raw == home:
        return "~"
    if raw.startswith(home + os.sep):
        return "~" + raw[len(home):]
    return raw


def record_hook(state: dict, event: str, payload: dict) -> dict:
    """Update a session's diagnostic record; return this invocation's heartbeat."""
    now = datetime.now(timezone.utc).isoformat()
    runtime = state.setdefault("runtime", {})
    from .install_state import identity
    runtime["package_identity"] = identity()
    if event == "prompt" and state.get("task_complete"):
        runtime["task_first_seen"] = now
        runtime["hook_events_seen"] = []
        runtime["heartbeats"] = []
        runtime.pop("diagnostic_tag", None)
        runtime.pop("diagnostic_tag_seen", None)
    runtime.setdefault("first_seen", now)
    runtime.setdefault("task_first_seen", now)
    runtime["last_seen"] = now
    runtime["cwd"] = _safe_cwd(payload.get("cwd"))
    runtime["plugin_root_present"] = bool(os.environ.get("PLUGIN_ROOT"))
    runtime["plugin_data_present"] = bool(os.environ.get("PLUGIN_DATA"))
    runtime["session_id_present"] = bool(payload.get("session_id"))
    runtime["turn_id_present"] = bool(payload.get("turn_id"))
    runtime["cwd_present"] = bool(payload.get("cwd"))
    seen = runtime.setdefault("hook_events_seen", [])
    hook = HOOKS[event]
    if hook not in seen:
        seen.append(hook)
    heartbeat = {
        "hook": hook,
        "timestamp": now,
        "session_id": _safe_text(payload.get("session_id")),
        "turn_id": _safe_text(payload.get("turn_id")),
        "cwd": runtime["cwd"],
    }
    if event == "tool":
        heartbeat["tool"] = _safe_text(payload.get("tool_name"), 80)
    if event == "stop":
        heartbeat["audit_created"] = False
    beats = runtime.setdefault("heartbeats", [])
    beats.append(heartbeat)
    del beats[:-HEARTBEAT_LIMIT]
    if event == "prompt":
        if isinstance(payload.get("prompt"), str) and SMOKE_MARKER in payload["prompt"]:
            runtime["diagnostic_tag"] = "desktop-smoke"
            runtime["diagnostic_tag_seen"] = now
    return heartbeat


def _data_root() -> Path:
    if os.environ.get("PLUGIN_DATA"):
        return Path(os.environ["PLUGIN_DATA"])
    current = codex_home() / "plugins" / "data" / "claim-verifier-personal"
    legacy = codex_home() / "plugin-data" / "claim-verifier"
    return current if current.is_dir() else legacy


def data_roots() -> list[Path]:
    if os.environ.get("PLUGIN_DATA"):
        return [Path(os.environ["PLUGIN_DATA"])]
    from .install_state import read_state
    try:
        recorded = read_state().get("data_root")
    except (OSError, ValueError):
        recorded = None
    roots = ([Path(recorded)] if isinstance(recorded, str) and Path(recorded).is_absolute() else [])
    roots.extend([codex_home() / "plugins/data/claim-verifier-personal",
                  codex_home() / "plugin-data/claim-verifier"])
    return list(dict.fromkeys(roots))


def read_ledgers() -> list[dict]:
    """Read private session files without mutating them or opening unrelated files."""
    states = []
    paths = dict.fromkeys(path.resolve() for root in data_roots() if root.is_dir() for path in root.glob("*.json"))
    for path in paths:
        if not re.fullmatch(r"[0-9a-f]{64}\.json", path.name):
            continue
        try:
            if path.stat().st_size > 10_000_000:
                continue
            value = json.loads(path.read_text())
            if (isinstance(value, dict) and isinstance(value.get("session_id"), str)
                    and isinstance(value.get("runtime", {}), dict)
                    and isinstance(value.get("audits", []), list)):
                states.append(value)
        except (OSError, ValueError, TypeError):
            continue
    return states


def read_desktop_observations() -> list[dict]:
    path = _data_root() / DESKTOP_OBSERVATIONS_FILE
    try:
        data = json.loads(path.read_text())
        return [item for item in data if isinstance(item, dict)
                and isinstance(item.get("session_id"), str)
                and item.get("receipt_visibility") in RECEIPT_VISIBILITY] if isinstance(data, list) else []
    except (OSError, ValueError, TypeError):
        return []


def record_desktop_observation(session_id: str, receipt_visibility: str) -> dict:
    """Store an explicit operator assertion of Desktop origin for a tagged session."""
    if receipt_visibility not in RECEIPT_VISIBILITY:
        raise ValueError("Invalid receipt visibility")
    state = next((item for item in read_ledgers() if item["session_id"] == session_id), None)
    if not state or state.get("runtime", {}).get("diagnostic_tag") != "desktop-smoke":
        raise ValueError("A tagged session with this ID was not found")
    root = _data_root()
    observations = [item for item in read_desktop_observations() if item.get("session_id") != session_id]
    record = {"session_id": session_id, "receipt_visibility": receipt_visibility,
              "recorded_at": datetime.now(timezone.utc).isoformat(), "provenance": "operator-supplied"}
    observations.append(record)
    observations = observations[-20:]
    fd, name = tempfile.mkstemp(dir=root, prefix=".desktop-observations-", text=True)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(observations, stream, separators=(",", ":"))
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(name, 0o600)
        os.replace(name, root / DESKTOP_OBSERVATIONS_FILE)
    finally:
        if os.path.exists(name):
            os.unlink(name)
    return record


def desktop_status(states: list[dict]) -> dict:
    observations = read_desktop_observations()
    if not observations:
        return {"hook_support": "INCONCLUSIVE", "receipt_visibility": "INCONCLUSIVE",
                "provenance": "NONE", "sessions": []}
    by_id = {state["session_id"]: state for state in states}
    matched = [by_id[item["session_id"]] for item in observations if item.get("session_id") in by_id]
    full_hooks = any(summarize_session(state)["observation"] == "OBSERVED" for state in matched)
    checked_run = any(
        any(event.get("checked_run", {}).get("exit_code") == 0 for event in state.get("events", [])
            if isinstance(event.get("checked_run"), dict))
        and any(claim.get("type") == "TEST_SUCCESS" and claim.get("status") == "VERIFIED"
                for audit in state.get("audits", []) for claim in audit.get("claims", []))
        for state in matched
    )
    support = "FULL" if full_hooks and checked_run else "PARTIAL" if matched else "NOT_OBSERVED"
    return {"hook_support": support, "receipt_visibility": observations[-1]["receipt_visibility"],
            "provenance": "operator-supplied", "sessions": [item["session_id"] for item in observations],
            "all_hooks_and_audit": full_hooks, "checked_run_verified": checked_run}


def latest_session(states: list[dict], *, tagged: bool = False, audit_only: bool = False) -> dict | None:
    candidates = [state for state in states
                  if (not tagged or state.get("runtime", {}).get("diagnostic_tag") == "desktop-smoke")
                  and (not audit_only or state.get("audits"))
                  and (not (tagged and audit_only) or
                       state["audits"][-1].get("timestamp", "") >=
                       state.get("runtime", {}).get("diagnostic_tag_seen", "~"))]
    if not candidates:
        return None
    return max(candidates, key=lambda state: (
        state.get("audits", [{}])[-1].get("timestamp", "") if audit_only else
        (state.get("runtime", {}).get("last_seen") or
         (state.get("audits", [{}])[-1].get("timestamp", "") if state.get("audits") else "")),
        state.get("session_id", ""),
    ))


def summarize_session(state: dict | None) -> dict:
    if not state:
        return {"observation": "NOT OBSERVED", "hook_events_seen": [], "audit_created": False}
    runtime = state.get("runtime", {})
    if not isinstance(runtime, dict):
        runtime = {}
    seen = [hook for hook in HOOKS.values() if hook in runtime.get("hook_events_seen", [])]
    audit_created = any(beat.get("hook") == "Stop" and beat.get("audit_created") is True
                        for beat in runtime.get("heartbeats", []))
    if not runtime and state.get("audits"):
        audit_created = True
    return {
        "session_id": state.get("session_id", ""),
        "first_seen": runtime.get("first_seen"),
        "task_first_seen": runtime.get("task_first_seen"),
        "last_seen": runtime.get("last_seen") or (state["audits"][-1].get("timestamp") if state.get("audits") else None),
        "diagnostic_tag": runtime.get("diagnostic_tag"),
        "cwd": runtime.get("cwd"),
        "plugin_root_present": runtime.get("plugin_root_present"),
        "plugin_data_present": runtime.get("plugin_data_present"),
        "session_id_present": runtime.get("session_id_present"),
        "turn_id_present": runtime.get("turn_id_present"),
        "cwd_present": runtime.get("cwd_present"),
        "hook_events_seen": seen,
        "heartbeats": runtime.get("heartbeats", []),
        "audit_created": audit_created,
        "diagnostics_available": bool(runtime),
        "observation": "OBSERVED" if len(seen) == 3 and audit_created else "INCONCLUSIVE",
    }


def doctor_status(cwd: str | None = None) -> dict:
    root = Path(__file__).resolve().parents[1]
    settings = load(cwd or os.getcwd())
    states = read_ledgers()
    package_present = (root / ".codex-plugin" / "plugin.json").is_file()
    installation = "INCONCLUSIVE"
    plugin_enabled = None
    installed_version = None
    try:
        listing = subprocess.run(["codex", "plugin", "list"], capture_output=True, text=True, timeout=8)
        if listing.returncode == 0:
            line = next((line for line in listing.stdout.splitlines()
                         if line.startswith("claim-verifier@personal ")), None)
            if line:
                fields = re.split(r"\s{2,}", line.strip())
                installation = "INSTALLED" if len(fields) > 1 and fields[1].startswith("installed") else "NOT OBSERVED"
                plugin_enabled = "enabled" in fields[1] if len(fields) > 1 else None
                installed_version = fields[2] if len(fields) > 2 else None
            else:
                installation = "NOT OBSERVED"
    except (OSError, subprocess.TimeoutExpired):
        pass
    return {
        "package_present": package_present,
        "installation": installation,
        "plugin_enabled": plugin_enabled,
        "installed_version": installed_version,
        "verifier_enabled": settings["enabled"],
        "level": settings["level"],
        "enforcement": settings["enforcement"],
        "hook_trust": "UNKNOWN",
        "recent_session": summarize_session(latest_session(states)),
        "tagged_smoke_session": summarize_session(latest_session(states, tagged=True)),
        "desktop": desktop_status(states),
    }


def latest_audit(*, tagged: bool = False) -> dict | None:
    state = latest_session(read_ledgers(), tagged=tagged, audit_only=True)
    if not state:
        return None
    audit = state["audits"][-1]
    return {
        "session_id": state["session_id"],
        "timestamp": audit.get("timestamp"),
        "started": state.get("runtime", {}).get("task_first_seen"),
        "hook_events_seen": summarize_session(state)["hook_events_seen"],
        "result": audit.get("result"),
        "level": audit.get("level"),
        "enforcement": audit.get("enforcement"),
        "diagnostic_tag": state.get("runtime", {}).get("diagnostic_tag"),
        "diagnostics_available": bool(state.get("runtime")),
        "claims": [{"claim": redact(str(item.get("claim", "")), 250), "type": item.get("type", ""),
                    "status": item.get("status", ""), "decision": item.get("decision", "")}
                   for item in audit.get("claims", [])],
        "footer_channel": (audit.get("footer") or {}).get("channel"),
        "footer": {key: value for key, value in (audit.get("footer") or {}).items()
                   if key in {"style", "rendered", "delivery", "channel"} and isinstance(value, str)},
    }
