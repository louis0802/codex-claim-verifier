"""Plugin-owned settings; Codex plugin activation remains in Codex config.toml."""
from __future__ import annotations

import os
import tomllib
from pathlib import Path

LEVELS = ("off", "receipts", "verify", "fresh", "complete", "strict")
ENFORCEMENT = ("report", "warn", "block")
FOOTER_STYLES = ("compact", "detailed", "failures-only", "adaptive")
FOOTER_DELIVERY = ("auto", "system-message", "problems-only")
DEFAULT = {
    "enabled": True,
    "level": "receipts",
    "enforcement": "report",
    "max_repair_attempts": 2,
    "model": {"enabled": True, "model": "gpt-6-luna", "reasoning_effort": "max", "only_for_ambiguous_claims": True},
    "footer": {"enabled": True, "style": "adaptive", "delivery": "auto", "show_level": True,
               "show_enforcement": False, "show_model": False, "show_evidence": False, "max_claims": 5},
}


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or (Path.home() / ".codex"))


def _read(path: Path) -> dict:
    if not path.is_file():
        return {}
    with path.open("rb") as stream:
        data = tomllib.load(stream)
    if not isinstance(data.get("claim_verifier", {}), dict):
        raise ValueError(f"Invalid claim_verifier section: {path}")
    return data.get("claim_verifier", {})


def _project_file(cwd: Path) -> Path | None:
    # Honor project-owned overrides only when Codex's user config marks the path trusted.
    try:
        with (codex_home() / "config.toml").open("rb") as stream:
            projects = tomllib.load(stream).get("projects", {})
    except FileNotFoundError:
        projects = {}
    trusted = False
    for path, settings in projects.items():
        if isinstance(settings, dict) and settings.get("trust_level") == "trusted":
            parent = Path(path).expanduser().resolve()
            if cwd == parent or cwd.is_relative_to(parent):
                trusted = True
                break
    if not trusted:
        return None
    # Use Git root where possible; non-Git tasks use their current directory.
    import subprocess
    proc = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=cwd, capture_output=True, text=True, timeout=3)
    root = Path(proc.stdout.strip()) if proc.returncode == 0 else cwd
    candidate = root / ".codex" / "claim-verifier.toml"
    return candidate if candidate.is_file() else None


def load(cwd: str, *, include_project: bool = True) -> dict:
    config = {**DEFAULT, "model": dict(DEFAULT["model"]), "footer": dict(DEFAULT["footer"])}
    files = [codex_home() / "claim-verifier.toml"]
    project = _project_file(Path(cwd).resolve()) if include_project else None
    if project:
        files.append(project)
    for path in files:
        values = _read(path)
        for key in ("enabled", "level", "enforcement", "max_repair_attempts"):
            if key in values:
                config[key] = values[key]
        config["model"].update(values.get("model", {}))
        footer = values.get("footer", {})
        if not isinstance(footer, dict):
            raise ValueError("footer must be a table")
        unknown = set(footer) - set(DEFAULT["footer"])
        if unknown:
            raise ValueError(f"Unknown footer settings: {', '.join(sorted(unknown))}")
        config["footer"].update(footer)
    if config["level"] not in LEVELS or config["enforcement"] not in ENFORCEMENT:
        raise ValueError("Invalid claim verifier level or enforcement")
    if type(config["max_repair_attempts"]) is not int or not 0 <= config["max_repair_attempts"] <= 10:
        raise ValueError("max_repair_attempts must be an integer from 0 to 10")
    for key in ("enabled",):
        if type(config[key]) is not bool:
            raise ValueError(f"{key} must be boolean")
    footer = config["footer"]
    if footer["style"] not in FOOTER_STYLES:
        raise ValueError("Invalid footer style")
    if footer["delivery"] not in FOOTER_DELIVERY:
        raise ValueError("Invalid or unsupported footer delivery")
    for key in ("enabled", "show_level", "show_enforcement", "show_model", "show_evidence"):
        if type(footer[key]) is not bool:
            raise ValueError(f"footer.{key} must be boolean")
    if type(footer["max_claims"]) is not int or not 1 <= footer["max_claims"] <= 20:
        raise ValueError("footer.max_claims must be an integer from 1 to 20")
    return config
