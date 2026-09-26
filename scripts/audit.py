#!/usr/bin/env python3
"""Inspect the latest structured Claim Verifier audit."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from claim_verifier.diagnostics import HOOKS, latest_audit


def render(audit: dict | None) -> str:
    if audit is None:
        return "No audit found."
    lines = ["Claim Verifier — Latest Audit", "", "Session", audit["session_id"][:12],
             "", "Started", str(audit["started"] or "unknown"),
             "", "Audit time", str(audit["timestamp"] or "unknown"), "", "Hooks"]
    for hook in HOOKS.values():
        indicator = "?" if not audit["diagnostics_available"] else ("✓" if hook in audit["hook_events_seen"] else "✗")
        lines.append(f"{indicator} {hook}")
    lines.extend(["", "Verification", str(audit["result"] or "unknown"), "", "Claims"])
    if not audit["claims"]:
        lines.append("None inspected")
    for claim in audit["claims"]:
        lines.append(f"{'✓' if claim['status'] == 'VERIFIED' else '✗'} {claim['claim']} — {claim['status']} ({claim['decision']})")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["latest"])
    parser.add_argument("--tagged", action="store_true", help="select latest desktop-smoke tagged audit")
    parser.add_argument("--json", action="store_true", help="print structured audit summary")
    args = parser.parse_args()
    audit = latest_audit(tagged=args.tagged)
    print(json.dumps(audit, indent=2) if args.json else render(audit))


if __name__ == "__main__":
    main()
