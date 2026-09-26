# Plan

1. [x] Inspect installed plugin, source, configuration, hooks, ledger, tests, and project guidance.
2. [x] Add bounded diagnostics to hook invocations and preserve verifier decisions.
3. [x] Add doctor and audit-latest readers and command adapters.
3a. [x] Add explicit Desktop provenance/receipt observation record and derived doctor status.
4. [x] Add focused regression tests for requirements 1-2.
5. [x] Run tests, manifest validation, and direct command checks; review changed files.
6. [x] Sync to local marketplace source and reinstall updated plugin.
7. [ ] Run CLI smoke checks in two directories and fresh desktop smoke tasks if available; record machine evidence and UI visibility. CLI A/B read-only tasks ran; neither produced a ledger. Automatic approval review rejected persistent hook trust, so trust and Desktop steps remain open.
8. [x] Update README and verification record with observed results and limitations.

Risk: A smoke marker appears in both CLI and desktop prompts, so it cannot establish surface provenance alone. Doctor must keep the desktop classification inconclusive until the live task is identified separately.
