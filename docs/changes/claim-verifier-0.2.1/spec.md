# v0.2.1 requirements

A1: A fresh isolated macOS setup without Codex installs npm-latest Codex and completes plugin installation, awaiting human review.
A2: Read-only plugin JSON commands retry exactly once only after successful exit with invalid JSON; valid second output continues.
A3: Persistent malformed JSON fails accurately with observed Codex version and manual retry command; verbose diagnostics are bounded and redact secrets. Nonzero commands retain checked failure behavior. Mutations are never automatically retried.
A4: Upgrade public 0.2.0 to 0.2.1 preserves complete/block configuration bytes and handles runtime identity conservatively.
A5: Tests pass without evidence remains UNVERIFIED/CORRECT.
A6: Successful live checked-run yields TEST_SUCCESS, VERIFIED/PASS.
A7: The verified live session observes UserPromptSubmit, PostToolUse, Stop.
A8: Doctor reports READY only with valid install/config/private storage, current runtime identity, expected hooks and audit, and no errors/attention.
A9: audit latest displays the stored footer; --json exposes selected audit and footer metadata, without raw hook output. Legacy missing footers remain readable. Delivery attempted is distinct from visible rendering.
A10: Verification commentary does not produce generic execution claims; direct execution assertions retain recall. Explicit corpus covers quotation, negation and uncertainty.

Keep level/enforcement meanings and no-evidence rule. Separate automated, distribution, trusted CLI and Desktop results. Require A1–A10 and package checks before tag/release. Human trust review remains external; missing evidence blocks publication, not independent implementation.
