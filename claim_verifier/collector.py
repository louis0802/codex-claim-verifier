"""Convert supported tool events to bounded evidence without trusting prose."""
from __future__ import annotations

import re
import subprocess
import base64
import json
import shlex
import hashlib
from pathlib import Path
from datetime import datetime, timezone


def redact(value: str, limit: int = 700) -> str:
    value = value[:limit]
    value = re.sub(r"(?i)(bearer\s+)[\w.\-]+", r"\1[REDACTED]", value)
    value = re.sub(r"(?i)\b([\w]*(?:token|secret|password|api_key)[\w]*\s*[=:]\s*)\S+", r"\1[REDACTED]", value)
    return value


def _response_parts(response):
    if isinstance(response, dict):
        code = response.get("exit_code", response.get("exitCode"))
        if type(code) is not int:
            code = None
        output = response.get("output", response.get("stdout", ""))
        if not output and isinstance(response.get("content"), list):
            output = "\n".join(str(item.get("text", "")) for item in response["content"] if isinstance(item, dict))
        output = str(output)
        if code is None:
            match = re.search(r"(?:Process exited with code|exit_code|exitCode)\s*[:=]?\s*(-?\d+)", output)
            code = int(match.group(1)) if match else None
        return code, output, str(response.get("stderr", ""))
    text = str(response or "")
    match = re.search(r"(?:Process exited with code|exit_code|exitCode)\s*[:=]?\s*(-?\d+)", text)
    return (int(match.group(1)) if match else None), text, ""


def _paths_from_patch(patch: str) -> tuple[list[str], list[str], list[str]]:
    created, written, deleted = [], [], []
    for kind, path in re.findall(r"^\*\*\* (Add|Update|Delete) File: (.+)$", patch, re.M):
        (created if kind == "Add" else deleted if kind == "Delete" else written).append(path.strip())
    return created, written, deleted


def collect(payload: dict) -> dict:
    name = str(payload.get("tool_name", ""))
    tool_input = payload.get("tool_input") or {}
    response = payload.get("tool_response")
    code, stdout, stderr = _response_parts(response)
    command = str(tool_input.get("command", "")) if isinstance(tool_input, dict) else ""
    checked_run = None
    if name == "Bash":
        try:
            tokens = shlex.split(command)
            expected_script = (Path(__file__).resolve().parents[1] / "scripts" / "checked_run.py").resolve()
            candidate = Path(tokens[1]).resolve() if len(tokens) >= 4 and tokens[0] in {"python", "python3"} and tokens[2] == "--" else None
            same_helper = bool(candidate and candidate.name == "checked_run.py" and candidate.is_file()
                               and candidate.stat().st_size <= 20000 and expected_script.is_file()
                               and hashlib.sha256(candidate.read_bytes()).digest() == hashlib.sha256(expected_script.read_bytes()).digest())
            if (len(tokens) >= 4 and tokens[0] in {"python", "python3"}
                    and same_helper and tokens[2] == "--"):
                marker = re.search(r"(?m)^CLAIM_VERIFIER_RECEIPT:([A-Za-z0-9+/=]{1,2048})$", stdout)
                if marker:
                    receipt = json.loads(base64.b64decode(marker.group(1), validate=True))
                    from .verify import CHECK_TYPES, command_kind
                    if (isinstance(receipt, dict) and receipt.get("command") == tokens[3:]
                            and type(receipt.get("exit_code")) is int
                            and receipt.get("kind") in CHECK_TYPES
                            and command_kind(shlex.join(tokens[3:])) == receipt["kind"]):
                        checked_run = {"kind": receipt["kind"], "exit_code": receipt["exit_code"]}
                        code = receipt["exit_code"]
                stdout = re.sub(r"(?m)^CLAIM_VERIFIER_RECEIPT:[A-Za-z0-9+/=]{1,2048}\n?", "", stdout, count=1)
        except (ValueError, OSError, json.JSONDecodeError):
            pass
    tool_succeeded = not (isinstance(response, dict) and response.get("isError")) and not re.search(r"^(?:Error:|Failed to |apply_patch failed)", stdout.strip(), re.I)
    paths = {"created": [], "written": [], "deleted": [], "read": []}
    if name == "apply_patch" and tool_succeeded and (code == 0 or re.search(r"\bSuccess\b", stdout, re.I)):
        a, b, c = _paths_from_patch(command)
        paths.update(created=a, written=b, deleted=c)
    elif isinstance(tool_input, dict):
        for key in ("path", "file_path", "filename"):
            if isinstance(tool_input.get(key), str):
                if re.search(r"(?:read|get|open)", name, re.I) and tool_succeeded:
                    paths["read"].append(tool_input[key])
                elif re.search(r"(?:write|edit|create)", name, re.I) and tool_succeeded and code != 1:
                    paths["written"].append(tool_input[key])
        if name == "Bash" and code == 0:
            # Conservative single-command detection; shell scripts/pipelines stay unverified.
            read = re.fullmatch(r"\s*(?:cat|head|tail|sed\s+-n)\s+([^;&|<>]+)\s*", command)
            if read:
                paths["read"].append(read.group(1).strip())
    git_state = {}
    if name == "Bash" and code == 0 and re.match(r"\s*git\s+(?:-\S+\s+)*commit\b", command):
        try:
            proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=payload.get("cwd") or None, capture_output=True, text=True, timeout=3)
            if proc.returncode == 0:
                git_state["commit"] = proc.stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            pass
    return {
        "event_id": str(payload.get("tool_use_id", "")),
        "turn_id": str(payload.get("turn_id", "")),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool": name,
        "cwd": str(payload.get("cwd", "")),
        "command": redact(command, 1200),
        "exit_code": code,
        "tool_succeeded": bool(tool_succeeded and (code is None or code == 0)),
        "response_meta": ({key: type(value).__name__ for key, value in response.items()} if isinstance(response, dict) else type(response).__name__),
        "transcript_path": str(payload.get("transcript_path") or ""),
        "transcript_exists": bool(payload.get("transcript_path") and Path(payload["transcript_path"]).is_file()),
        "stdout_summary": redact(stdout),
        "stderr_summary": redact(stderr),
        "paths": paths,
        "git_state": git_state,
        "checked_run": checked_run,
    }
