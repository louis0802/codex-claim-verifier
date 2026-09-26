#!/usr/bin/env python3
"""Agent-invoked local validation wrapper that emits an exit-status receipt.

The Stop hook may suggest this command, but never invokes it. Codex runs it via
the ordinary shell tool and permission flow. Only recognized validation commands
are accepted; the wrapper has no shell interpretation.
"""
from __future__ import annotations

import base64
import json
import shlex
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from claim_verifier.verify import CHECK_TYPES, command_kind

MARKER = "CLAIM_VERIFIER_RECEIPT:"


def main() -> int:
    args = sys.argv[1:]
    if args and args[0] == "--":
        args = args[1:]
    kind = command_kind(shlex.join(args)) if args else None
    if kind not in CHECK_TYPES:
        print("checked_run accepts only recognized test, build, lint, or typecheck commands.", file=sys.stderr)
        return 2
    try:
        proc = subprocess.run(args, capture_output=True, text=True, errors="replace")
        code, out, err = proc.returncode, proc.stdout, proc.stderr
    except FileNotFoundError as exc:
        code, out, err = 127, "", str(exc)
    receipt = {"kind": kind, "command": args, "exit_code": code}
    encoded = base64.b64encode(json.dumps(receipt, separators=(",", ":")).encode()).decode()
    print(MARKER + encoded, flush=True)
    if out:
        print(out[-10000:], end="" if out.endswith("\n") else "\n")
    if err:
        print(err[-10000:], end="" if err.endswith("\n") else "\n", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
