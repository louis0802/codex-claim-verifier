# Execution and verification plan

- [x] Inspect original source, personal marketplace, installed JSON records, hook integration, existing diagnostics and commands.
- [x] Write four consistent change documents before application edits.
- [x] Implement setup state/identity/private storage and hook completion integration (A4,A5).
- [x] Implement dependency-free Node CLI, runtime bootstrap/launcher, safe Codex installation, marketplace staging/config/bootstrap/onboarding (A1-A3,A7-A9).
- [x] Add public Python diagnostics/audit bridge while preserving legacy CLI and verification behavior (A5,A6).
- [x] Add fresh/second/custom/existing/upgrade/PATH/npm/non-TTY/dry-run/security/activation/failure tests (A1-A9).
- [x] Rewrite README entry UX; document dependencies, sources, release and product limitations; add verified commands to AGENTS.md.
- [x] Run existing + new unittest suite, Node tests, plugin validation, npm package validation, isolated real-Codex install/idempotency smoke, packaged npx smoke; review diff and acceptance criteria; record evidence in verification.md.

Risks: marketplace/API versions differ; detect unsupported JSON commands and report actionable errors. Installer downloads need network; test failures explicitly. Existing plugin predating activation integration stays installed and needs --upgrade. Portable Python pins need deliberate maintenance and include upstream attribution. Real human trust flow cannot be automated in tests.

Material discoveries: real marketplace sources must stay inside HOME, requiring alternate staging for external CODEX_HOME; macOS system /var and /tmp aliases require a narrow directory-check exception. Regression tests cover both. Real isolated Codex 0.155.0-alpha.2.6 and npm-installed 0.157.1 reached the human trust boundary; portable CPython 3.13.15 installation passed. Account sign-in and actual human hook review remain external requirements.

Verification complete: 59 Python tests, 26 Node tests, syntax/plugin/package checks, real isolated installs, portable runtime and actual npx tarball smoke passed. See verification.md for scope and release gates. npm bin symlink handling now has regression coverage and repository guidance.
