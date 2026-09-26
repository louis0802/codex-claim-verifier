# Design

Existing Node setup uses checked and parseJSON in cli/system.mjs; ensureCodex observes version but discards it. Retain version in context. Add an allowlisted read-only JSON helper with exact parsing and one retry; use bounded secret-redacted diagnostics shared with checked errors. Keep mutating marketplace-add single attempt and fail explicitly on ambiguous JSON, with manual inspection guidance.

scripts/public_cli.py bridges Python diagnostics to Node. Extend latest_audit's selected fields with stored footer metadata; render in scripts/audit.py without verification/model calls. Expose Node audit latest --json, preserving old list/text behavior. Add explicit hook names to verbose doctor using current-identity observations.

claims.py currently sends any sentence containing verified to semantic normalization. Filter narrow verification-meta/uncertainty forms before generic ambiguity, preserving direct claims and existing negation handling. Regression corpus states exact extraction and counts before/after. No evidence-decision changes.

Use release/v0.2.1, explicit user-requested version (no development suffix), isolated installation homes. Historical docs and v0.2.0 assets remain immutable. Build tarball only after tests; stable and alpha smoke separately. Upgrade preserves config without migration. Release only after authentic trusted acceptance. Rollback uses existing immutable v0.2.0; never reuses a version for changed payload.

Review refinement: split semicolon and comma-and clauses so an uncertainty clause
cannot hide a subsequent direct assertion. Stored footer channel none is presented
as stored only, without claiming delivery. Audit JSON projects only four string
footer fields and retains the legacy footer_channel field.
