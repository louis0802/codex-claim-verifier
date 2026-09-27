# Published v0.2.1 distribution verification

Verified 2026-09-27 on macOS arm64.

Release: https://github.com/louis0802/codex-claim-verifier/releases/tag/v0.2.1
GitHub release ID: 397479851. Public, prerelease, not draft.
Annotated tag v0.2.1 points to 0428e495ac9d3ba581c4ff497d40e5be7d8bffb5.

Assets: claim-verifier-0.2.1.tgz and checksums.txt.
SHA-256: 6965c7a37551b5157f83a878d054374b885251247e2a7ef517f1fc1f37d7d965

Both public downloads, without authentication, exactly matched local files.
GitHub's asset digest matched the local SHA-256. The tarball contains 31 files,
each equal to the tagged source, with no private/generated/nested archive content.

## Public setup and upgrade

A fresh isolated HOME, CODEX_HOME and npm cache, with Codex absent from PATH,
installed stable codex-cli 0.157.1 through @openai/codex@latest and installed
Claim Verifier using the public v0.2.1 tarball. Plugin JSON parsed exactly.
Version reported 0.2.1; doctor remained WAITING FOR HOOK REVIEW as required.
Empty audit latest --json returned null. The actual public repository marketplace
was separately installed pinned to v0.2.1 and verified through Codex listing.

In a separate clean home, setup first installed the public v0.2.0 package. Config
was customized to complete/block, then the public v0.2.1 tarball ran setup
--upgrade. Plugin version became 0.2.1; config bytes and mtime were preserved.
Doctor remained waiting, hook_trust UNKNOWN, no invented readiness or hook activity.
No GitHub credentials were passed to these smoke processes.

These isolated distribution checks are distinct from the actual human-reviewed
CLI sessions documented in live-acceptance.md, where doctor reached READY.

## Immutability and remaining limits

v0.2.0 tag, assets and historical records were untouched. v0.2.1 assets and tag
are immutable. Postpublication main changes update only README/evidence documents;
they do not replace the tagged package. npm remains unpublished.
Desktop trusted lifecycle and physical x64 execution remain pending. Native
final-answer insertion is unsupported; systemMessage visibility is not guaranteed.
