# Public distribution verification — v0.2.0

## Immutable source and assets

- Repository: [louis0802/codex-claim-verifier](https://github.com/louis0802/codex-claim-verifier)
- Annotated tag: [v0.2.0](https://github.com/louis0802/codex-claim-verifier/tree/v0.2.0)
- Tagged source commit: `aa4a8848f2d1c419172c0c5dc5cbf502dabf2455`
- Release: [Codex Claim Verifier v0.2.0 — Public Preview](https://github.com/louis0802/codex-claim-verifier/releases/tag/v0.2.0)
- Public pre-release status: verified through the unauthenticated GitHub API
- Assets: `claim-verifier-0.2.0.tgz` and `checksums.txt`
- Tarball SHA-256: `e3c80d124226bd5d5626d7bdf62a041194148a159e26fe6aee3a98c0e5c93c34`

GitHub main matched the initial source commit before tagging. All 31 package
files matched committed bytes before upload. Server-side asset sizes and digests
matched local files. Both release assets were then downloaded without credentials
and matched local files byte for byte. The public annotated tag resolves to the
same source commit. The tag and published assets were not rewritten.

This evidence was recorded after publication in a documentation-only follow-up
commit on main. The npm package payload and application/runtime code are unchanged
from the tagged source; the new evidence documents are excluded from the tarball.

## Actual public installation

The README's GitHub release URL was used as the package source in a fresh npm
cache and isolated user/Codex home. Child processes had GitHub credential variables
removed. No local release/source path was used to install the package.

| Public check | Observed result |
| --- | --- |
| npx setup from HTTPS release asset | Passed; installed plugin 0.2.0 through actual Codex CLI |
| Repeated setup | Passed; exact custom configuration bytes and modification time preserved |
| version | CLI 0.2.0, plugin 0.2.0, config schema 1 |
| doctor before human trust | Expected exit 1; WAITING FOR HOOK REVIEW, no false READY |
| audit latest / audit list | Passed; no audit invented |
| setup dry-run | Passed; preserved existing config |
| Installed notices | LICENSE and THIRD_PARTY.md matched source |
| Explicit GitHub marketplace at v0.2.0 | Actual Codex fetched the public repo/ref and installed claim-verifier@codex-claim-verifier 0.2.0 |
| Configuration across source upgrade | Preserved; hook trust stayed UNKNOWN; ready stayed false |

The setup calls used `--no-launch` to stop before interactive Codex onboarding.
The public installation and remote marketplace checks used real npm/npx and
Codex 0.158.0-alpha.2.1. The verifier's automated baseline is **86 passed tests**
(59 Python, 27 Node), with plugin/package/syntax validation passed.

## Tracking issues

- [Native final-answer footer support](https://github.com/louis0802/codex-claim-verifier/issues/1)
- [Reliable shell exit status in Codex hooks](https://github.com/louis0802/codex-claim-verifier/issues/2)
- [Trusted-session Desktop validation](https://github.com/louis0802/codex-claim-verifier/issues/3)
- [Stronger Stop/final-response enforcement](https://github.com/louis0802/codex-claim-verifier/issues/4)

## Remaining manual acceptance

Human `/hooks` trust was neither performed nor changed. The fresh trusted fake
claim, successful checked-run claim, and doctor READY acceptance remain pending.
Trusted Desktop lifecycle delivery and visible receipts also remain pending. These
are disclosed Public Preview limitations, not results inferred from unit tests or
installation. Physical x64 runtime execution remains unverified on this arm64 host.
No npm publication occurred. Optional CI was deferred.
