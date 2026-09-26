# Claim Verifier footer: plan

1. Inspect hook/config/store/tests and run a live `Stop → systemMessage` probe. Done: CLI warning was absent from normal and JSON output, though the ledger recorded the audit. Choose `auto → problems-only` given the documented warning presentation.
2. Add and validate footer configuration, including trusted project merge and unsupported native mode. Done.
3. Implement a pure renderer with exact output strings, ordering, limits, privacy controls, model-call flag, and optional evidence summaries. Done.
4. Connect renderer to Stop audit storage and a presentation adapter without changing `verify.py` decisions. Keep report/warn/block behavior, repair budget, and task reset. Done. `verify.py` acquired presentation-safe `path` and evidence `source` fields without changing factual decisions.
5. Add targeted renderer and hook integration tests. Run the full unit suite and plugin validator. Done: 38 tests and manifest validation passed.
6. Live smoke test from two directories using the updated installed plugin. Done with a one-off trust bypass: problem and PASS receipts were stored, but neither appeared in CLI JSON output. An ordinary task in directory A skipped hooks because trust has not been persisted. Desktop presentation remains unmeasured.
7. Update README, example TOML, existing change docs as necessary, and a verification record. Compare final behavior with spec, flag runtime limits, update personal plugin via cachebuster/reinstall. Done for code and documentation; final tests and plugin validation passed. Ordinary-session smoke remains pending the user's hook trust review.

## Risks
Stop `systemMessage` may remain invisible in CLI. Its UI presentation is warning styled, so default auto omits clean-pass delivery. The current hook does not provide a native final-answer footer. Hook trust is independent of installation. Raw audit evidence must never be rendered directly.

## Material deviation
The user's target experience requires a verifier-owned receipt visibly appended to every final answer. The current Stop API cannot append or rewrite final text. The CLI did not display emitted `systemMessage` receipts, and ordinary tasks skip the hook pending user trust review. The implementation guarantees rendering and storage when the hook runs; visible final-answer delivery remains a Codex runtime limitation.
