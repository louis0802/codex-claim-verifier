"""Hook orchestration: the only outward action is feedback to the main Codex agent."""
from __future__ import annotations

from datetime import datetime, timezone

from .claims import extract
from .collector import collect
from .config import load
from .diagnostics import MISSING_SESSION, record_hook
from .footer import presentation_message, render_footer
from .semantic import normalize
from .store import ledger
from .verify import evaluate


def _risk(kind: str) -> str:
    if kind in {"TEST_SUCCESS", "BUILD_SUCCESS", "LINT_SUCCESS", "TYPECHECK_SUCCESS"}:
        return "LOCAL_VALIDATION"
    if kind in {"FILE_MODIFIED", "FILE_CREATED", "FILE_DELETED", "GIT_COMMIT_CREATED"}:
        return "LOCAL_MUTATION"
    if kind in {"GIT_PUSH_COMPLETED", "PR_CREATED"}:
        return "REMOTE_MUTATION"
    if kind == "DEPLOYMENT_COMPLETED":
        return "HIGH_IMPACT"
    return "READ_ONLY"


def _feedback(finding: dict) -> str:
    action = finding["decision"]
    if action == "REPAIR":
        advice = "Complete the user-required work using the normal Codex tools and permissions, then report its actual result."
    elif action == "DISCLOSE":
        advice = "Disclose the uncertainty or unfinished work accurately."
    else:
        advice = "Correct or remove the unsupported claim, or gather real evidence through the normal Codex tools."
    if finding["type"] in {"TEST_SUCCESS", "BUILD_SUCCESS", "LINT_SUCCESS", "TYPECHECK_SUCCESS"} and finding["status"] == "INCONCLUSIVE":
        from pathlib import Path
        helper = Path(__file__).resolve().parents[1] / "scripts" / "checked_run.py"
        advice += f" If the check already ran but its exit status was unavailable, rerun it with: python3 {helper} -- <check command and arguments>."
    return (
        "Claim Verifier: " + action + ". " +
        f"Claim: {finding['claim'][:250]} " +
        f"Evidence status: {finding['status']}. " +
        f"Action class: {_risk(finding['type'])}. " + advice
    )


def handle(event: str, payload: dict, semantic_normalize=normalize) -> dict | None:
    result = _handle(event, payload, semantic_normalize)
    from .install_state import record_success
    try:
        record_success(event, str(payload.get("session_id") or ""))
    except (OSError, ValueError, TypeError, KeyError):
        # Observation failure cannot change a verification decision or invent readiness.
        pass
    return result


def _handle(event: str, payload: dict, semantic_normalize=normalize) -> dict | None:
    if event not in {"prompt", "tool", "stop"}:
        return {"systemMessage": "Claim Verifier: unknown hook event"}
    session = str(payload.get("session_id") or "")
    cwd = str(payload.get("cwd") or ".")
    with ledger(session or MISSING_SESSION) as state:
        heartbeat = record_hook(state, event, payload)
        if not session:
            return {"systemMessage": "Claim Verifier: missing session id; audit inconclusive"}
        config = load(cwd)
        if not config["enabled"] or config["level"] == "off":
            return None
        if event == "prompt":
            prompt = payload.get("prompt")
            if isinstance(prompt, str):
                if state.get("task_complete"):
                    state["prompts"] = []
                    state["repair_attempts"] = 0
                    state["task_complete"] = False
                state["prompts"].append(prompt[:10000])
                state["prompts"] = state["prompts"][-30:]
            return None
        if event == "tool":
            receipt = collect(payload)
            if not any(old.get("event_id") == receipt["event_id"] and receipt["event_id"] for old in state["events"]):
                state["events"].append(receipt)
                state["events"] = state["events"][-1000:]
            return None

        final_text = str(payload.get("last_assistant_message") or "")
        claims, ambiguous = extract(final_text)
        model_ok = True
        model_used = bool(ambiguous and config["model"].get("enabled", True))
        if ambiguous:
            more, model_ok = (semantic_normalize(state["prompts"][0] if state["prompts"] else "", ambiguous, config["model"])
                              if model_used else ([], False))
            claims.extend(more)
            normalized = {item["text"] for item in more}
            claims.extend(
                {"type": "GENERIC_VERIFIED", "text": item, "origin": "semantic_unavailable" if not model_ok else "semantic_omitted"}
                for item in ambiguous if item not in normalized
            )
        findings = evaluate(claims, state["events"], state["prompts"], config["level"], cwd)
        blockers = [item for item in findings if item["decision"] != "PASS"]
        severity = {"REPAIR": 0, "CORRECT": 1, "DISCLOSE": 2}
        blockers.sort(key=lambda item: severity.get(item["decision"], 3))
        exhausted = state["repair_attempts"] >= config["max_repair_attempts"] or bool(payload.get("stop_hook_active"))
        if exhausted and blockers:
            for item in blockers:
                item["decision"] = "DISCLOSE"
        result = blockers[0]["decision"] if blockers else "PASS"
        next_attempt = state["repair_attempts"] + (1 if blockers and config["enforcement"] == "block" and not exhausted else 0)
        audit = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "turn_id": str(payload.get("turn_id") or ""),
            "level": config["level"],
            "enforcement": config["enforcement"],
            "claim_model": {"model": config["model"].get("model"), "reasoning_effort": config["model"].get("reasoning_effort"), "available": model_ok, "used": model_used},
            "result": result,
            "claims": findings,
            "repair_attempts": next_attempt,
            "max_repair_attempts": config["max_repair_attempts"],
        }
        footer_config = config["footer"]
        if blockers and config["enforcement"] == "warn" and footer_config["style"] != "failures-only":
            footer_config = {**footer_config, "style": "detailed"}
        rendered = render_footer(audit, footer_config)
        if footer_config["enabled"]:
            audit["footer"] = {"style": footer_config["style"], "rendered": rendered,
                               "delivery": footer_config["delivery"], "channel": "none"}
        state["audits"].append(audit)
        state["audits"] = state["audits"][-50:]
        heartbeat["audit_created"] = True
        message = presentation_message(audit, rendered, footer_config)
        if not blockers or config["enforcement"] == "report":
            state["task_complete"] = True
            if message:
                audit["footer"]["channel"] = "systemMessage"
            return {"systemMessage": message} if message else None
        feedback = _feedback(blockers[0])
        if config["enforcement"] == "warn" or exhausted:
            state["task_complete"] = True
            if message:
                audit["footer"]["channel"] = "systemMessage"
            return {"systemMessage": message or feedback}
        state["repair_attempts"] = next_attempt
        if message:
            audit["footer"]["channel"] = "continuation-reason"
        return {"decision": "block", "reason": feedback + ("\n\n" + message if message else "")}
