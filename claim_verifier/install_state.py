"""Private installation observations; never reads or writes Codex hook trust."""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from .config import codex_home

EXPECTED = ("UserPromptSubmit", "PostToolUse", "Stop")
EVENTS = dict(zip(("prompt", "tool", "stop"), EXPECTED))
SCHEMA = 1


def identity(root: Path | None = None) -> str:
    root = root or Path(__file__).resolve().parents[1]
    digest = hashlib.sha256()
    files = [root / ".codex-plugin" / "plugin.json"]
    # Match the Node payload identity while supporting legacy packages without notices.
    files.extend(root / name for name in ("LICENSE", "THIRD_PARTY.md") if (root / name).is_file())
    for directory in ("claim_verifier", "hooks", "scripts"):
        files.extend(p for p in (root / directory).rglob("*")
                     if p.is_file() and p.suffix in {".py", ".json", ".mjs"} and "__pycache__" not in p.parts)
    for path in sorted(files, key=lambda p: p.relative_to(root).as_posix()):
        digest.update(path.relative_to(root).as_posix().encode() + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def state_path() -> Path:
    return codex_home() / "claim-verifier-installation.json"


def read_state() -> dict:
    try:
        value = json.loads(state_path().read_text())
        if not isinstance(value, dict) or value.get("schema_version") != SCHEMA:
            raise ValueError("Invalid installation state schema")
        return value
    except FileNotFoundError:
        return {}


def initialize(root: Path, version: str, data_root: Path, selector: str = "claim-verifier@personal") -> dict:
    path = state_path()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    lock_path = path.with_suffix(".lock")
    if path.is_symlink() or lock_path.is_symlink():
        raise ValueError("Installation state must not be symlinked")
    with lock_path.open("a+") as lock:
        os.chmod(lock_path, 0o600)
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = read_state()
        current = identity(root)
        if state.get("identity") != current:
            state = {"schema_version": SCHEMA, "plugin": "claim-verifier", "identity": current,
                     "hooks_seen": [], "audit_created": False, "hook_activity": "NOT_OBSERVED", "ready": False}
        state.update(installed=True, installed_version=version, hook_trust="UNKNOWN", selector=selector)
        if not state.get("setup_at"):
            state["setup_at"] = datetime.now(timezone.utc).isoformat()
        state.setdefault("data_root", str(data_root.resolve()))
        content = json.dumps(state, separators=(",", ":"))
        if path.exists() and path.read_text() == content:
            return state
        fd, name = tempfile.mkstemp(dir=path.parent, prefix=".claim-verifier-state-")
        try:
            with os.fdopen(fd, "w") as output:
                output.write(content)
                output.flush()
                os.fsync(output.fileno())
            os.replace(name, path)
        finally:
            if os.path.exists(name):
                os.unlink(name)
        return state


def record_success(event: str, session_id: str) -> None:
    """Called after hook handling and ledger commit, never by setup or user confirmation."""
    if event not in EVENTS or not session_id:
        return
    from .store import data_dir
    root = data_dir()
    ledger_path = root / (hashlib.sha256(session_id.encode()).hexdigest() + ".json")
    ledger = json.loads(ledger_path.read_text())
    beat = ledger.get("runtime", {}).get("heartbeats", [{}])[-1]
    if beat.get("hook") != EVENTS[event]:
        return
    path = state_path()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    lock_path = path.with_suffix(".lock")
    if path.is_symlink() or lock_path.is_symlink():
        raise ValueError("Installation state must not be symlinked")
    with lock_path.open("a+") as lock:
        os.chmod(lock_path, 0o600)
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = read_state()
        current = identity()
        # An old task must not undo a new installation's observation boundary.
        if state and state.get("identity") != current:
            return
        version = json.loads((Path(__file__).resolve().parents[1] / ".codex-plugin/plugin.json").read_text())["version"]
        state = state or {"schema_version": SCHEMA, "plugin": "claim-verifier", "installed": True,
                          "installed_version": version, "identity": current, "hooks_seen": [],
                          "audit_created": False, "setup_at": None}
        now = datetime.now(timezone.utc).isoformat()
        seen = set(state.get("hooks_seen", []))
        seen.add(EVENTS[event])
        state.update(hooks_seen=[hook for hook in EXPECTED if hook in seen],
                     hook_trust="UNKNOWN", hook_activity="OBSERVED", last_hook_at=now,
                     data_root=str(root.resolve()))
        state["audit_created"] = bool(state.get("audit_created") or
                                      (event == "stop" and beat.get("audit_created") is True and ledger.get("audits")))
        if event == "stop" and beat.get("audit_created") is True and ledger.get("audits"):
            state["audit_session_id"] = session_id
        state["ready"] = len(state["hooks_seen"]) == len(EXPECTED) and state["audit_created"]
        fd, name = tempfile.mkstemp(dir=path.parent, prefix=".claim-verifier-state-")
        try:
            with os.fdopen(fd, "w") as output:
                json.dump(state, output, separators=(",", ":"))
                output.flush()
                os.fsync(output.fileno())
            os.replace(name, path)
        finally:
            if os.path.exists(name):
                os.unlink(name)
