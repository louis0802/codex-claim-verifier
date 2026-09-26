# Requested implementation mapping

1. Packaging: Python plugin, legacy .codex-plugin manifest; hooks/hooks.json, hook Python entry point, no npm package.
2. Marketplace: personal implicit ~/.agents/plugins/marketplace.json with local source ~/plugins/claim-verifier; installed copy under Codex plugins/cache/personal/claim-verifier/<version>.
3. Doctor: claim_verifier/diagnostics.py doctor_status, scripts/doctor.py legacy rendering.
4. Audit: latest_audit/read_ledgers and scripts/audit.py latest; list is new.
5. Public Node CLI: root cli/ plus package.json; same repo avoids unnecessary workspaces.
6. Programmatic installation: codex plugin add claim-verifier@personal --json; explicit non-default marketplace sources use codex plugin marketplace add SOURCE --json [--ref REF].
7. Versions: manifest version has base 0.1.0 plus timestamp cachebuster; use plugin-creator helper for source update; npm CLI package release version separate.
8. Existing install: codex plugin list --json installed[] records, selector, version, enabled; verify cached manifest/runtime payload exists.
9. Reliable states: executable available/version, installed/enabled plugin reported by Codex, validated payload/config/storage, actual hook completion and persisted audit for current identity.
10. Human-controlled: /hooks review/trust and account login. Do not read or write trust records; report UNKNOWN while using actual hook observations for readiness.
11. Files: package.json, cli/*.mjs and python-downloads.json; hooks/run.mjs/hooks.json/claim_verifier.py; claim_verifier/install_state.py, diagnostics.py, store.py; scripts/public_cli.py; Python and Node tests; README/AGENTS; five change documents. No verification algorithm changes.
12. Limitations: macOS/Node entry requirement, existing Python 3.11+ dependency resolved by verified portable runtime; unsupported older Codex APIs fail with upgrade guidance; npm publication and true human trust smoke are separate release/security steps. A new unauthenticated user may need Codex sign-in in addition to hook review.

Sources: https://developers.openai.com/plugins/build/plugins ; https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex ; https://docs.astral.sh/uv/concepts/python-versions/ . Actual local CLI help confirms plugin add/list JSON support.
