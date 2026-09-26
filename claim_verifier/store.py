"""Small, private per-session JSON ledger with atomic writes and locking."""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path


def data_dir() -> Path:
    from .config import codex_home
    path = Path(os.environ.get("PLUGIN_DATA") or codex_home() / "plugin-data" / "claim-verifier")
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError("Audit storage must not be symlinked")
    os.chmod(path, 0o700)
    return path


def _path(session_id: str) -> Path:
    key = hashlib.sha256(session_id.encode()).hexdigest()
    return data_dir() / f"{key}.json"


@contextmanager
def ledger(session_id: str):
    path = _path(session_id)
    lock = path.with_suffix(".lock")
    with lock.open("a+") as stream:
        os.chmod(lock, 0o600)
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        state = json.loads(path.read_text()) if path.exists() else {
            "session_id": session_id, "events": [], "prompts": [], "audits": [], "repair_attempts": 0
        }
        yield state
        fd, name = tempfile.mkstemp(dir=path.parent, prefix=".ledger-", text=True)
        try:
            with os.fdopen(fd, "w") as output:
                json.dump(state, output, separators=(",", ":"))
                output.flush()
                os.fsync(output.fileno())
            os.replace(name, path)
            os.chmod(path, 0o600)
        finally:
            if os.path.exists(name):
                os.unlink(name)
