# Execution and verification

- [x] Inspect main, v0.2.0, guidance and implementation; reproduce baseline (59 Python + 27 Node, syntax pass).
- [x] Write consistent intent/spec/design/plan before code.
- [x] Add failing regressions for A2/A3, A9, A10; capture failures and corpus baseline.
- [x] Implement focused JSON diagnostics, audit visibility and extraction changes; bump version and README.
- [x] Run full tests, syntax, plugin validation and diff review; record exact counts.
- [x] Pack/inspect 0.2.1; stable fresh-install and public 0.2.0 upgrade smoke (A1/A4), alpha separately.
- [ ] Record user-reported fake case separately; perform authentic trusted checked-run and doctor (A5–A8), requiring human review when needed.
- [ ] Synchronize evidence/docs; logical commits, merge main, immutable tag and GitHub prerelease with checksum after gates pass. Public upgrade verification; no npm publication.

Risks: real client startup differs from fixtures; output can contain secrets; runtime identity changes require review; authenticated live execution may need user interaction. Optional mutation reconciliation and helper-path feedback are excluded unless evidence shows necessary.

## Current evidence and deviations

96 tests pass (63 Python, 33 Node); exact package has 31 files and retained notices.
Stable 0.157.1 was installed from npm latest in an isolated PATH with no Codex.
Both stable and alpha 0.158.0-alpha.2.1 passed personal/repository setup and the
public 0.2.0 upgrade. Final stable artifact was rerun after review fixes.
Self-review found stored channel none mislabeling and uncertainty clause recall;
regressions failed first and now pass. No independent review is claimed.
The core verifier, collector, semantic adapter, footer renderer, install identity,
hook definitions and checked-run helper match v0.2.0 byte for byte.

The candidate is installed globally via normal setup --upgrade; config bytes and
mtime preserved. Setup reports WAITING FOR HOOK REVIEW for the changed identity.
Human review was requested; no trust records or bypass flags were used. Release
and main merge remain gated. Draft release notes/checksum are outside the repo.
Optional mutation reconciliation was unnecessary: marketplace-add ambiguity fails
with inspection guidance, while plugin-add is followed by a state check.
