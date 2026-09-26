"""Deterministic evidence checks and cumulative policy decisions."""
from __future__ import annotations

import os
import re
import shlex
import subprocess
from pathlib import Path

from .claims import explicit_requirements

CHECK_TYPES = {"TEST_SUCCESS", "BUILD_SUCCESS", "LINT_SUCCESS", "TYPECHECK_SUCCESS"}
FILE_TYPES = {"FILE_READ": "read", "FILE_MODIFIED": "written", "FILE_CREATED": "created", "FILE_DELETED": "deleted"}


def _tokens(command: str) -> list[str]:
    if re.search(r"[;&|<>\n]", command):
        return []
    try:
        return shlex.split(command)
    except ValueError:
        return []


def command_kind(command: str) -> str | None:
    t = _tokens(command)
    if not t:
        return None
    while t and re.match(r"^[A-Za-z_][\w]*=", t[0]):
        t.pop(0)
    if not t:
        return None
    if t[:2] == ["git", "commit"] or (t[0] == "git" and "commit" in t[:4]):
        return "GIT_COMMIT_CREATED"
    if t[:2] == ["git", "push"] or (t[0] == "git" and "push" in t[:4]):
        return "GIT_PUSH_COMPLETED"
    if t[0] in {"pytest", "py.test", "nosetests"} or t[:3] == ["python", "-m", "pytest"]:
        return "TEST_SUCCESS"
    if t[0] in {"npm", "pnpm", "yarn", "bun"}:
        joined = " ".join(t[1:3])
        for word, kind in (("test", "TEST_SUCCESS"), ("build", "BUILD_SUCCESS"), ("lint", "LINT_SUCCESS"), ("typecheck", "TYPECHECK_SUCCESS"), ("type-check", "TYPECHECK_SUCCESS")):
            if re.search(r"\b" + word + r"\b", joined):
                return kind
    if t[0] == "dotnet" and len(t) > 1:
        return {"test": "TEST_SUCCESS", "build": "BUILD_SUCCESS"}.get(t[1])
    if t[0] == "cargo" and len(t) > 1:
        return {"test": "TEST_SUCCESS", "build": "BUILD_SUCCESS", "check": "TYPECHECK_SUCCESS", "clippy": "LINT_SUCCESS"}.get(t[1])
    if t[0] == "go" and len(t) > 1:
        return {"test": "TEST_SUCCESS", "build": "BUILD_SUCCESS", "vet": "LINT_SUCCESS"}.get(t[1])
    if t[0] in {"make", "just"} and len(t) > 1:
        return {"test": "TEST_SUCCESS", "build": "BUILD_SUCCESS", "lint": "LINT_SUCCESS", "typecheck": "TYPECHECK_SUCCESS"}.get(t[1])
    if t[0] in {"mypy", "pyright", "tsc"}:
        return "TYPECHECK_SUCCESS"
    if t[0] in {"ruff", "eslint", "flake8"}:
        return "LINT_SUCCESS"
    return None


def _same_path(claimed: str, observed: str, cwd: str) -> bool:
    try:
        base = Path(cwd or os.getcwd())
        return (base / claimed).resolve() == (base / observed).resolve()
    except OSError:
        return False


def _git(cwd: str, *args: str) -> str | None:
    try:
        result = subprocess.run(["git", *args], cwd=cwd or None, capture_output=True, text=True, timeout=5)
        return result.stdout.strip() if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def _remote_matches(cwd: str) -> bool | None:
    upstream = _git(cwd, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    head = _git(cwd, "rev-parse", "HEAD")
    if not upstream or not head or "/" not in upstream:
        return None
    remote, branch = upstream.split("/", 1)
    try:
        result = subprocess.run(["git", "ls-remote", "--heads", remote, branch], cwd=cwd or None, capture_output=True, text=True, timeout=6)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    hashes = [line.split()[0] for line in result.stdout.splitlines() if line.strip()]
    return head in hashes


def status(claim: dict, events: list[dict], level: str, cwd: str) -> tuple[str, dict | None]:
    kind = claim["type"]
    if kind in CHECK_TYPES | {"GIT_COMMIT_CREATED", "GIT_PUSH_COMPLETED"}:
        matching = [(i, e) for i, e in enumerate(events) if e.get("tool") == "Bash" and (command_kind(e.get("command", "")) == kind or (e.get("checked_run") or {}).get("kind") == kind)]
        if not matching:
            return "UNVERIFIED", None
        index, event = matching[-1]
        code = event.get("exit_code")
        receipt = {"event_id": event.get("event_id"), "command": event.get("command"), "exit_code": code,
                   "source": "checked_run" if event.get("checked_run") else "PostToolUse"}
        if code is None:
            if level == "receipts" and kind in CHECK_TYPES and re.search(r"\b(?:\d+ passed|tests? passed|build succeeded|lint passed|type[ -]?check passed)\b", event.get("stdout_summary", ""), re.I):
                receipt["strength"] = "output-only"
                return "VERIFIED", receipt
            return "INCONCLUSIVE", receipt
        if code != 0:
            return "FALSE", receipt
        if kind in CHECK_TYPES and level in {"fresh", "complete", "strict"}:
            for later in events[index + 1:]:
                paths = later.get("paths", {})
                if any(paths.get(k) for k in ("created", "written", "deleted")):
                    return "STALE", receipt
        if kind == "GIT_COMMIT_CREATED":
            commit = event.get("git_state", {}).get("commit")
            if not commit or _git(cwd, "cat-file", "-t", commit) != "commit":
                return "INCONCLUSIVE", receipt
            receipt["commit"] = commit
        if kind == "GIT_PUSH_COMPLETED":
            remote = _remote_matches(cwd)
            if remote is None:
                return "INCONCLUSIVE", receipt
            if not remote:
                return "FALSE", receipt
        return "VERIFIED", receipt
    if kind in FILE_TYPES:
        claimed = claim.get("path")
        if not claimed:
            return "INCONCLUSIVE", None
        bucket = FILE_TYPES[kind]
        for event in reversed(events):
            if any(_same_path(claimed, path, event.get("cwd") or cwd) for path in event.get("paths", {}).get(bucket, [])):
                if level != "receipts":
                    exists = (Path(cwd) / claimed).exists()
                    if kind == "FILE_DELETED" and exists:
                        return "FALSE", {"event_id": event.get("event_id"), "path": claimed}
                    if kind in {"FILE_CREATED", "FILE_MODIFIED"} and not exists:
                        return "FALSE", {"event_id": event.get("event_id"), "path": claimed}
                return "VERIFIED", {"event_id": event.get("event_id"), "path": claimed}
        return "UNVERIFIED", None
    if kind == "INSPECTION_PERFORMED":
        for event in reversed(events):
            if event.get("paths", {}).get("read"):
                return "VERIFIED", {"event_id": event.get("event_id")}
        return "UNVERIFIED", None
    if kind == "PR_CREATED":
        for event in reversed(events):
            if re.search(r"(?:create_pr|create_pull_request|gh pr create)", event.get("tool", "") + " " + event.get("command", ""), re.I):
                if event.get("tool_succeeded") and re.search(r"https?://\S+/pull/\d+", event.get("stdout_summary", "")):
                    return "VERIFIED", {"event_id": event.get("event_id")}
        return "UNVERIFIED", None
    # Broad statements and deployment require authoritative checks not supplied by the MVP.
    return "INCONCLUSIVE", None


def evaluate(claims: list[dict], events: list[dict], prompts: list[str], level: str, cwd: str) -> list[dict]:
    results = []
    required = explicit_requirements(prompts) if level in {"complete", "strict"} else set()
    for kind in sorted(required):
        if not any(claim["type"] == kind for claim in claims):
            claims.append({"type": kind, "text": f"Required by user task: {kind}", "origin": "task"})
    for claim in claims:
        factual, evidence = status(claim, events, level, cwd)
        task_required = claim["type"] in required
        if factual == "VERIFIED":
            decision = "PASS"
        elif task_required:
            decision = "REPAIR"
        elif factual == "INCONCLUSIVE" and level == "strict":
            decision = "DISCLOSE"
        else:
            decision = "CORRECT"
        results.append({"claim": claim["text"], "type": claim["type"], "path": claim.get("path"), "status": factual,
                        "decision": decision, "task_required": task_required, "evidence": evidence})
    return results
