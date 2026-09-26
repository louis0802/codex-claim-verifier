# Claim Verifier footer: design

## Existing system and probe
`hook.py` composes extraction, optional Luna normalization, `verify.evaluate`, the repair budget, and the per-session `store.ledger`. Findings contain type, claim, status, decision, task_required, and a bounded evidence object. The ledger already retains 50 audits. No evidence decision needs to move into presentation.

The installed Codex CLI `0.155.0-alpha.2.6` was probed with `receipts + warn` and `Tests pass.` with no test event. The audit recorded `CORRECT/UNVERIFIED`, but normal CLI output ended with the model's text and JSON output contained only an `agent_message`; neither showed the returned warning. The official hook contract calls `systemMessage` a UI warning and offers no final-text replacement. Desktop presentation remains unmeasured.

## Components and contracts
- `config.py` adds validated `[claim_verifier.footer]` defaults: enabled, style, delivery, show_level, show_enforcement, show_model, show_evidence, max_claims. Trusted project override merges footer keys. `native` is rejected at load time.
- `footer.py` is pure: audit plus footer config become a deterministic presentation model and string. It does not read files, invoke a model, inspect Git, or mutate findings. Counts and heading derive from structured statuses/results; hostile claim/evidence text is redacted, made one line, and capped. Evidence only uses allowlisted structured fields.
- `hook.py` records whether Luna was called, computes audit/result as before, records the repair attempt count and limit, renders once, stores `{style, rendered, delivery, channel}` beside the audit, then asks a small delivery adapter for hook output. `channel` is `none`, `systemMessage`, or `continuation-reason`; it records emission rather than guaranteeing UI visibility. For block, the existing advice is retained and a rendered repair receipt can be attached to the continuation reason; it is never represented as a final pass.
- The adapter maps `auto` to problems-only on this runtime. `system-message` sends all non-repair receipts through `systemMessage`; `problems-only` and auto send only problem receipts. Report mode never blocks. Warn mode returns a receipt when there is a problem. Block mode preserves decision/block or exhausted disclosure behavior.

## Privacy and failure handling
File paths and claim text are untrusted. Renderer strips controls/line breaks, applies the existing redaction function plus conservative token/key patterns, and truncates to at most 120 characters for a raw label. Evidence shows event IDs and exit status only, not commands or output. The authoritative structured audit remains unchanged except for added presentation metadata. An invalid footer setting causes the hook's existing configuration warning, not a false pass.

## Rollout
Install by the personal-marketplace cachebuster flow. Keep global verification policy at `receipts + report` and set footer `adaptive + auto`. New tasks load the updated plugin. Roll back by disabling footer in TOML or reinstalling the earlier plugin. Persistent hook trust remains a user review step; one-off probe bypasses do not establish it.

## Source
[Codex hook contract](https://learn.chatgpt.com/docs/hooks).
