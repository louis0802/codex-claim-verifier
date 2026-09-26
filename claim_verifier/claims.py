"""Deterministic claim extraction, with optional semantic normalization."""
from __future__ import annotations

import re

PATTERNS = [
    ("TEST_SUCCESS", r"\b(?:(?:all )?tests? (?:all )?(?:pass(?:ed)?|are green|succeed(?:ed)?)|(?:pytest|dotnet test|npm test|cargo test|go test) (?:pass(?:ed)?|succeed(?:ed)?))\b"),
    ("BUILD_SUCCESS", r"\b(?:build (?:pass(?:ed)?|succeed(?:ed)?|is successful|works)|(?:built|compiled) successfully)\b"),
    ("LINT_SUCCESS", r"\b(?:lint(?:ing)? (?:pass(?:ed)?|succeed(?:ed)?|is clean)|no lint errors)\b"),
    ("TYPECHECK_SUCCESS", r"\b(?:type[ -]?check(?:ing)? (?:pass(?:ed)?|succeed(?:ed)?|is clean)|no type errors)\b"),
    ("GIT_COMMIT_CREATED", r"\b(?:I |we )?(?:committed|created (?:a )?commit)\b"),
    ("GIT_PUSH_COMPLETED", r"\b(?:I |we )?(?:pushed|push(?:ed)? (?:the )?branch)\b"),
    ("PR_CREATED", r"\b(?:I |we )?(?:opened|created) (?:a )?(?:PR|pull request)\b"),
    ("DEPLOYMENT_COMPLETED", r"\b(?:I |we )?deployed\b"),
    ("FILE_CREATED", r"\b(?:I |we )?(?:created|added)\s+([\w./-]+\.[\w-]+)\b"),
    ("FILE_MODIFIED", r"\b(?:I |we )?(?:updated|modified|edited|changed)\s+([\w./-]+\.[\w-]+)\b"),
    ("FILE_DELETED", r"\b(?:I |we )?(?:deleted|removed)\s+([\w./-]+\.[\w-]+)\b"),
    ("FILE_READ", r"\b(?:I |we )?(?:read|inspected|reviewed)\s+([\w./-]+\.[\w-]+)\b"),
]
AMBIGUOUS = re.compile(r"\b(?:verified|fully verified|everything works|no regressions|backwards? compatible|remains compatible|contract remains|reviewed|completed|fixed)\b", re.I)
NEGATED = re.compile(r"\b(?:did not|didn't|have not|haven't|could not|couldn't|not yet|unable to|failed to)\b", re.I)


# Narrow epistemic disclosures: these do not assert the embedded proposition.
UNCERTAIN = re.compile(r"^(?:I|we) (?:cannot|can't|could not|couldn't|am unable to|are unable to) verify\b", re.I)
META_VERIFICATION = re.compile(
    r"^(?:the (?:requested closing text|following statement) is (?:not a verified result|unverified)"
    r"|claim verifier (?:marked|classified|reported) (?:this|that|the statement) as \w+)[.:]?$", re.I)


def extract(answer: str) -> tuple[list[dict], list[str]]:
    claims, ambiguous = [], []
    for raw in re.split(r"(?<=[.!?])\s+|\n+|;\s*|,\s+and\s+|\s+\bbut\b\s+|\s+\bhowever\b\s+", answer, flags=re.I):
        sentence = raw.strip().lstrip("-* ")
        if not sentence or NEGATED.search(sentence) or UNCERTAIN.search(sentence):
            continue
        found = False
        for kind, pattern in PATTERNS:
            match = re.search(pattern, sentence, re.I)
            if match:
                claim = {"type": kind, "text": sentence}
                if match.lastindex:
                    claim["path"] = match.group(1)
                claims.append(claim)
                found = True
        if not found and not META_VERIFICATION.fullmatch(sentence) and AMBIGUOUS.search(sentence):
            ambiguous.append(sentence)
    return claims, ambiguous


def explicit_requirements(prompts: list[str]) -> set[str]:
    """Conservative explicit intent only. Later user cancellations clear requirements."""
    requirements = set()
    verbs = {
        "TEST_SUCCESS": r"\b(?:run|execute|rerun) (?:the |all |relevant )?tests?\b",
        "BUILD_SUCCESS": r"\b(?:run|verify|check) (?:the )?build\b|\bbuild (?:the )?project\b",
        "LINT_SUCCESS": r"\b(?:run|check) (?:the )?lint(?:er)?\b",
        "TYPECHECK_SUCCESS": r"\b(?:run|check) (?:the )?type[ -]?check\b",
        "GIT_COMMIT_CREATED": r"\b(?:commit|create a commit)\b",
        "GIT_PUSH_COMPLETED": r"\bpush\b",
    }
    for prompt in prompts:
        for kind, pattern in verbs.items():
            if re.search(r"\b(?:do not|don't|no need to|skip)\b.{0,30}" + pattern, prompt, re.I):
                requirements.discard(kind)
            elif re.search(pattern, prompt, re.I):
                requirements.add(kind)
    return requirements
