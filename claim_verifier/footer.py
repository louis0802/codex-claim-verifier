"""Pure, deterministic rendering of structured Claim Verifier audits."""
from __future__ import annotations

import re
from collections import Counter

from .collector import redact

LABELS = {
    "TEST_SUCCESS": "Tests", "BUILD_SUCCESS": "Build", "LINT_SUCCESS": "Lint",
    "TYPECHECK_SUCCESS": "Typecheck", "GIT_COMMIT_CREATED": "Commit",
    "GIT_PUSH_COMPLETED": "Push", "PR_CREATED": "Pull request",
    "DEPLOYMENT_COMPLETED": "Deployment", "INSPECTION_PERFORMED": "Inspection",
}
FILE_VERBS = {"FILE_CREATED": "created", "FILE_MODIFIED": "modified",
              "FILE_DELETED": "deleted", "FILE_READ": "read"}
SYMBOLS = {"VERIFIED": "✓", "FALSE": "✗", "UNVERIFIED": "✗",
           "INCONCLUSIVE": "△", "STALE": "◷"}
PRIORITY = {"FALSE": 1, "STALE": 2, "UNVERIFIED": 3, "INCONCLUSIVE": 4, "VERIFIED": 5}


def _safe(value: object, limit: int = 120) -> str:
    text = str(value or "")
    text = re.sub(r"[\x00-\x1f\x7f\u2028\u2029]+", " ", text)
    text = redact(text, max(limit * 4, 700))
    text = re.sub(r"(?i)\b(?:sk|ghp|gho|github_pat)-?[A-Za-z0-9_]{12,}\b", "[REDACTED]", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"


def _label(item: dict) -> str:
    kind = item.get("type", "")
    if kind in FILE_VERBS:
        path = item.get("path") or (item.get("evidence") or {}).get("path")
        if path:
            return f"{_safe(path, 100)} {FILE_VERBS[kind]}"
    if kind in LABELS:
        return LABELS[kind]
    return f'"{_safe(item.get("claim"), 120)}"'


def _result(audit: dict) -> str:
    claims = audit.get("claims", [])
    unresolved = [x for x in claims if x.get("status") != "VERIFIED"]
    result = audit.get("result", "CORRECT")
    if not unresolved:
        return "PASS"
    if result == "PASS":
        return "CORRECT"
    return result if result in {"CORRECT", "REPAIR", "DISCLOSE"} else "CORRECT"


def _header(audit: dict) -> str:
    result = _result(audit)
    if result == "PASS":
        return "✓ Claim Verifier · PASS"
    if result == "REPAIR":
        return "↻ Claim Verifier · REPAIR"
    if result == "DISCLOSE":
        return "⚠ Claim Verifier · DISCLOSE"
    statuses = {x.get("status") for x in audit.get("claims", []) if x.get("status") != "VERIFIED"}
    if statuses == {"STALE"}:
        return "◷ Claim Verifier · STALE"
    return "⚠ Claim Verifier · CORRECT"


def _counts(audit: dict) -> Counter:
    return Counter(x.get("status", "INCONCLUSIVE") for x in audit.get("claims", []))


def render_compact(audit: dict, config: dict) -> str:
    claims = audit.get("claims", [])
    counts = _counts(audit)
    result = _result(audit)
    if result == "PASS":
        return "✓ Claim Verifier · PASS · 0 claims checked" if not claims else f"✓ Claim Verifier · PASS · {counts['VERIFIED']}/{len(claims)} verified"
    attempts = audit.get("repair_attempts", 0)
    limit = audit.get("max_repair_attempts", 0)
    if result == "REPAIR":
        return f"↻ Claim Verifier · REPAIR · attempt {attempts}/{limit}"
    if result == "DISCLOSE":
        return f"⚠ Claim Verifier · DISCLOSE · attempts {attempts}/{limit}"
    unsupported = len(claims) - counts["VERIFIED"] - counts["STALE"]
    pieces = [f"{counts['VERIFIED']} verified"] if counts["VERIFIED"] else []
    if counts["STALE"]:
        pieces.append(f"{counts['STALE']} stale")
    if unsupported:
        pieces.append(f"{unsupported} unsupported")
    symbol = "◷" if counts["STALE"] and not unsupported else "⚠"
    return f"{symbol} Claim Verifier · " + " · ".join(pieces)


def _evidence(item: dict) -> str | None:
    evidence = item.get("evidence")
    if not isinstance(evidence, dict):
        return None
    source = evidence.get("source")
    code = evidence.get("exit_code")
    if source == "checked_run" and type(code) is int:
        return f"Evidence: checked_run · exit {code}"
    event_id = evidence.get("event_id")
    if event_id:
        suffix = " · output only" if evidence.get("strength") == "output-only" else ""
        return f"Evidence: PostToolUse event {_safe(event_id, 48)}{suffix}"
    return None


def _rows(audit: dict, config: dict) -> list[str]:
    claims = sorted(audit.get("claims", []), key=lambda x: (0 if x.get("task_required") and x.get("status") != "VERIFIED" else PRIORITY.get(x.get("status"), 4),))
    lines = []
    for item in claims[:config["max_claims"]]:
        status = item.get("status", "INCONCLUSIVE")
        lines.append(f"{SYMBOLS.get(status, '△')} {_label(item)} · {status}")
        if item.get("task_required") and status != "VERIFIED":
            lines.append("  Required by user task.")
        elif status == "STALE":
            lines.append("  Validation occurred before subsequent code changes.")
        if config["show_evidence"]:
            evidence = _evidence(item)
            if evidence:
                lines.append("  " + evidence)
    more = len(claims) - config["max_claims"]
    if more > 0:
        lines.append(f"… {more} more claims in audit ledger")
    return lines


def render_detailed(audit: dict, config: dict, *, failures_only: bool = False) -> str:
    heading = "⚠ Claim Verifier" if failures_only else _header(audit)
    lines = [heading]
    rows = _rows(audit, config)
    if rows:
        lines.extend(["", *rows])
    elif _result(audit) == "PASS":
        lines.extend(["", "No execution claims checked."])
    metadata = []
    if config["show_level"] and not failures_only:
        metadata.append(f"Level: {_safe(audit.get('level'), 32)}")
    if config["show_enforcement"]:
        metadata.append(f"Enforcement: {_safe(audit.get('enforcement'), 32)}")
    model = audit.get("claim_model") or {}
    if config["show_model"] and model.get("used"):
        slug = model.get("model")
        name = "GPT-6 Luna" if slug == "gpt-6-luna" else _safe(slug, 50)
        effort = _safe(model.get("reasoning_effort"), 20)
        metadata.append(f"Claim extraction: {name} · {effort}" + (" (unavailable)" if not model.get("available") else ""))
    result = _result(audit)
    if result in {"REPAIR", "DISCLOSE"}:
        word = "Repair attempt" if result == "REPAIR" else "Repair attempts"
        metadata.append(f"{word}: {audit.get('repair_attempts', 0)}/{audit.get('max_repair_attempts', 0)}")
    if metadata:
        lines.extend(["", *metadata])
    return "\n".join(lines)


def render_adaptive(audit: dict, config: dict) -> str:
    return render_compact(audit, config) if _result(audit) == "PASS" else render_detailed(audit, config)


def render_footer(audit: dict, config: dict) -> str:
    """Render only existing audit data; never perform verification here."""
    if not config["enabled"]:
        return ""
    style = config["style"]
    if style == "compact":
        return render_compact(audit, config)
    if style == "detailed":
        return render_detailed(audit, config)
    if style == "failures-only":
        return "" if _result(audit) == "PASS" else render_detailed(audit, config, failures_only=True)
    return render_adaptive(audit, config)


def presentation_message(audit: dict, footer: str, config: dict) -> str | None:
    """Current-runtime adapter; native final-answer insertion is unavailable."""
    if not footer:
        return None
    if config["delivery"] == "system-message":
        return footer
    return footer if _result(audit) != "PASS" else None
