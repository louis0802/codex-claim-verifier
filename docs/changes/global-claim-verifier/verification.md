# Verification record

- Plugin manifest validator: passed.
- Python unit tests: 18 passed, including acceptance scenarios A–H, trusted project override, semantic-model failure, false command output, task-boundary reset, and validation receipt behavior.
- GPT-6 Luna/max CLI invocation: succeeded with the exact requested model and reasoning effort; semantic adapter returned a structured compatibility claim and did not verify it.
- Live Codex CLI smoke A: personal plugin loaded from a new directory; `UserPromptSubmit` and `Stop` ran; ledger marked an unrun test claim `UNVERIFIED`.
- Live Codex CLI smoke B: second directory's project override set `receipts + block`; `Stop` requested a correction. With a one-attempt budget, Codex repeated the false claim after continuation. This confirms block is advisory after the budget.
- Live `PostToolUse` smoke: `pwd` and failing `false` commands produced only model-facing stdout in `tool_response`; no exit status or transcript path was supplied to the hook. This is why stronger levels require the agent-invoked checked-run receipt for shell validation.
- Live checked-run smoke: Codex ran `python3 ~/plugins/claim-verifier/scripts/checked_run.py -- make test` in a fresh task. The `PostToolUse` ledger recorded `TEST_SUCCESS`, exit code `0`; `verify` marked `Tests pass` as `VERIFIED`.
- Hook trust: smoke tasks used the one-off, vetted `--dangerously-bypass-hook-trust` flag. Persistent hook trust still requires the user's `/hooks` review.
- The later footer extension has its own [verification record](../claim-verifier-footer/verification.md); it does not change the original evidence decisions.
