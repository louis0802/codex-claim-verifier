# Requirements

## User journey

1. Install the updated local plugin and trust its three hooks in `/hooks` if needed.
2. Start a fresh Codex task with the published smoke marker, first in CLI and then in ChatGPT desktop.
3. Run `python3 scripts/doctor.py` and `python3 scripts/audit.py latest` from the plugin. Select the tagged task when testing multiple sessions.
4. Record whether each hook ran, whether Stop wrote an audit, whether checked-run evidence verified a real test result, and whether a receipt appeared in the UI.

## Behavior

- Each hook invocation records its event name, timestamp, available ID presence, sanitized cwd, and safe tool name. Stop also records whether it generated an audit.
- A session runtime summary records first seen, environment-variable presence, hook stages seen, and the diagnostic tag. The marker has no effect on verification decisions.
- Doctor reports installation and effective configuration, latest tagged and general session activity, and an explicit unknown trust state unless trust is independently established.
- Doctor uses `OBSERVED`, `NOT OBSERVED`, or `INCONCLUSIVE` for hook observations. It must never infer the launch surface from the prompt marker.
- Audit latest prints the most recent audit's session, time, hook stages, result, and concise claim statuses. JSON output is available for automation.
- The tool treats missing activity as `NOT OBSERVED`, not as proof that desktop hooks are unsupported. Partial activity is identified by stage.
- Footer visibility is recorded only from a live UI inspection; a `systemMessage` emitted by a hook does not prove visibility.
- An operator may attach a known desktop origin and observed receipt visibility to an existing tagged diagnostic session. Doctor identifies that provenance as operator supplied, then derives hook/evidence status from the stored ledger.

## Acceptance criteria

1. Tests cover heartbeat persistence, marker tagging, latest selection, partial and absent stages, output, and no false desktop inference.
2. Existing tests pass and verification decisions match pre-change behavior.
3. A fresh CLI smoke task in each of two directories has a corresponding diagnostic/audit record when hooks are trusted.
4. Fresh desktop tasks test ordinary reading, unsupported test-success claim, and checked-run verification. Record observed results, including unavailable steps, without guessing.
5. README and verification record make installation, trust, execution, and receipt visibility distinct.
6. Doctor can show a classified Desktop result after a known tagged session is recorded, while leaving unrecorded sessions inconclusive.

## Open decision

There is no confirmed hook payload field that attests "launched from ChatGPT desktop." Until observed, the operator associates a known fresh desktop task with its diagnostic session; the CLI must label desktop provenance `INCONCLUSIVE` by itself.
