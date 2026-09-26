#!/usr/bin/env python3
"""Read-only Claim Verifier installation and hook diagnostics."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from claim_verifier.diagnostics import HOOKS, doctor_status


def render(status: dict) -> str:
    install_marker = "✓" if status["installation"] == "INSTALLED" else "?" if status["installation"] == "INCONCLUSIVE" else "✗"
    lines = ["Claim Verifier Doctor", "", "Installation", f"{'✓' if status['package_present'] else '✗'} package found",
             f"{install_marker} claim-verifier@personal: {status['installation']}",
             f"Version: {status['installed_version'] or 'unknown'}",
             f"{'✓' if status['plugin_enabled'] else '✗' if status['plugin_enabled'] is False else '?'} plugin enabled: {status['plugin_enabled']}",
             "", "Verifier configuration", f"{'✓' if status['verifier_enabled'] else '✗'} {'enabled' if status['verifier_enabled'] else 'disabled'}",
             f"✓ level: {status['level']}", f"✓ enforcement: {status['enforcement']}",
             "", "Hook trust", "? UNKNOWN — review /hooks in Codex CLI"]
    for label, key in (("Recent hook activity", "recent_session"), ("Tagged smoke session", "tagged_smoke_session")):
        session = status[key]
        lines.extend(["", label])
        if session["observation"] == "NOT OBSERVED":
            lines.append("✗ No hook activity observed")
            continue
        lines.append(f"Session: {session['session_id'][:12]} · {session.get('last_seen') or 'time unknown'}")
        if not session["diagnostics_available"]:
            lines.append("? Hook diagnostics unavailable in this older ledger")
            lines.append(f"{'✓' if session['audit_created'] else '?'} audit generated")
            continue
        for hook in HOOKS.values():
            lines.append(f"{'✓' if hook in session['hook_events_seen'] else '✗'} {hook}")
        lines.append(f"{'✓' if session['audit_created'] else '✗'} audit generated")
        lines.append(f"Hook observation: {session['observation']}")
    desktop = status["desktop"]
    lines.extend(["", "ChatGPT Desktop", f"Hook support: {desktop['hook_support']}",
                  f"Receipt visibility: {desktop['receipt_visibility']}",
                  f"Surface provenance: {desktop['provenance']}"])
    if desktop["provenance"] == "NONE":
        lines.append("Use record_desktop.py after inspecting a known fresh Desktop task; marker alone is insufficient.")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print structured status")
    args = parser.parse_args()
    status = doctor_status()
    print(json.dumps(status, indent=2) if args.json else render(status))


if __name__ == "__main__":
    main()
