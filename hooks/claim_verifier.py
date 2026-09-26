#!/usr/bin/env python3
"""Codex command hook entry point; reads one JSON event from stdin."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from claim_verifier.hook import handle


def main():
    try:
        payload = json.load(sys.stdin)
        result = handle(sys.argv[1] if len(sys.argv) > 1 else "", payload)
        if result:
            print(json.dumps(result, separators=(",", ":")))
    except Exception as exc:
        # Hook failures never turn missing evidence into a successful verification.
        print(json.dumps({"systemMessage": f"Claim Verifier could not complete its audit: {type(exc).__name__}"}))


if __name__ == "__main__":
    main()
