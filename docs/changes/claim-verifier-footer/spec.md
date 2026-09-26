# Claim Verifier footer: specification

## User behavior
- Each completed Stop audit gets a deterministic, bounded receipt stored with that audit. Disabling the footer stores no rendered receipt and emits no footer.
- Four styles exist: `compact`, `detailed`, `failures-only`, and `adaptive` (default). Adaptive uses one line for a clean pass and detail for any problem. Failures-only emits no text for a clean pass.
- A clean pass with zero claims must say that zero claims were checked, never imply that all task work was verified. Claim counts come only from audit claims.
- Detailed receipts list required repairs first, then false, stale, unverified, inconclusive, and verified claims. They cap rows at `max_claims` and state how many remain. A cap cannot hide the existence of a problem.
- Receipts label known claim types, show safe file paths when available, and truncate/redact unknown claim text. Evidence and model details are opt-in. Model details appear only when a semantic model was actually called.
- Repair attempts show the current attempt and budget. An exhausted repair with unresolved claims says `DISCLOSE`, never `PASS`; a later successful audit replaces that with a pass receipt.
- `report` does not change the Stop decision. `warn` surfaces a problem receipt. `block` keeps its existing continuation behavior and can include the repair receipt in the continuation reason. The latest audit is the source for the latest receipt.

## Delivery decision
`auto` is the default. Because the current `systemMessage` surface is a warning, auto emits problem receipts through that channel and stores successful receipts without showing a warning. `system-message` explicitly emits every non-repair receipt through the supported channel. `problems-only` emits only problem receipts. `native` is reserved and rejected until Codex supplies a native footer API. No mode asks the main model to write the receipt.

## Acceptance
Exact-string tests cover all styles, statuses, mixed results, zero/one/multiple claims, repair retries and exhaustion, truncation, privacy, model/evidence switches, disabled footer, and enforcement interaction. Existing verifier tests and plugin validation pass. Live CLI probes in two directories record whether hook delivery appears in text or JSON output and whether ordinary trusted hooks run.

## Open runtime limitation
Current Codex may not show a Stop `systemMessage` as an independent final-answer item. A rendered and stored receipt is guaranteed when the hook runs; user-visible placement is not guaranteed by this plugin.
