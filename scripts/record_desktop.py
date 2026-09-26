#!/usr/bin/env python3
"""Record a known Desktop smoke session after inspecting its live UI."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from claim_verifier.diagnostics import RECEIPT_VISIBILITY, record_desktop_observation


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session_id", help="full tagged session ID from doctor --json")
    parser.add_argument("--receipt-visibility", choices=RECEIPT_VISIBILITY, default="INCONCLUSIVE")
    args = parser.parse_args()
    try:
        record = record_desktop_observation(args.session_id, args.receipt_visibility)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(record, indent=2))
    print("Desktop origin is operator-supplied; hook and audit results come from the ledger.")


if __name__ == "__main__":
    main()
