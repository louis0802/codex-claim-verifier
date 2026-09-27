# v0.2.1 verification

Status: released; automated, public distribution and trusted CLI acceptance verified separately.
Host: macOS arm64, Node 24.13.1, Python 3.11.5. Baseline main equals origin/main
83475d896458ff5c08f1fef508608d99a44b31a2; v0.2.0 differs only in historical release docs.

## Automated

Baseline 59 Python + 27 Node = 86 passing tests. New regressions failed before
fixes (persistent/transient JSON, receipt projection/rendering, meta extraction).
Final current suite: 63 Python + 33 Node = 96, all pass. npm run check passes.
Plugin Creator validator passes. Tests cover no retry on nonzero exit or mutation,
exact JSON parsing, version diagnostics, bounded redaction, stored receipt text
and JSON, legacy ledgers, stored-only delivery, trust preservation, current
identity readiness, and evidence outcomes. No verifier decision engine changes.

Corpus (16 cases; deterministic typed claims plus ambiguity candidates):
- v0.2.0: 9 true positives, 6 false positives, 0 false negatives.
- v0.2.1: 9 true positives, 0 false positives, 0 false negatives.

Direct execution recall is preserved. New clause-boundary cases ensure a later
assertion survives an earlier uncertainty disclosure. Assertions are extraction
candidates, never evidence of truth.

## Distribution compatibility

| Client | Plugin JSON | Personal/repository marketplace | Fresh setup | Public 0.2.0 upgrade |
| --- | --- | --- | --- | --- |
| npm latest stable 0.157.1 | exact parse passed | passed | installed Codex from absent PATH; awaiting review | passed |
| development 0.158.0-alpha.2.1 | exact parse passed | passed | existing alpha; awaiting review | passed |

Both isolated upgrades preserved complete/block config bytes and mtime. Neither
invented readiness or trust. Stable was obtained by actual @openai/codex@latest
installation. No noisy startup happened in these real runs; simulated regressions
cover it. The v0.2.1 input was local, v0.2.0 input was the public GitHub asset.
Public v0.2.1 download, fresh setup, pinned marketplace and upgrade now pass;
see distribution.md for postpublication evidence.

npm pack uses a workspace-local cache (default cache was sandbox-inaccessible).
31 files inspected against source; no private/generated/nested archives. Final candidate was repacked after review, all 31 files matched source, and
the exact artifact passed stable fresh/upgrade smoke again. Global installation
preserved config bytes and mtime and reports WAITING FOR HOOK REVIEW.

## Live acceptance

See live-acceptance.md for actual 2026-09-27 output, user-confirmed review and
sandbox distinctions. Fresh stable CLI checked-run: 33 Node tests pass, current
runtime TEST_SUCCESS VERIFIED/PASS, all three hooks, doctor READY. Separate fresh
no-evidence fixture: UNVERIFIED/CORRECT, prompt/Stop only as expected.
Stored receipt text and JSON agree. systemMessage visibility was not established.
User-reported prior evidence remains attributed separately. Desktop and physical
x64 remain pending; native final insertion unsupported. No npm publication.
