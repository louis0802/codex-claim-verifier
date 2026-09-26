# Claim Verifier development

- `claim_verifier/` implements settings, evidence collection, claim extraction, verification, and hook decisions. `hooks/run.mjs` launches `hooks/claim_verifier.py`, the Python hook entry point; `scripts/checked_run.py` is invoked by the main Codex agent, never by the hook.
- Use `python3 -m unittest discover -s tests -v` and the plugin-creator `validate_plugin.py` before packaging.
- Do not treat model output or ordinary Bash stdout as a successful exit status. The current Codex Bash hook omits process status; the checked-run receipt supplies it for local validation.
- Keep `Stop` repair instructions bounded and truthful. Its block result creates a continuation prompt and does not provide an absolute final veto.
- Footer rendering is a pure view over the structured audit. `systemMessage` is a warning channel, and the tested CLI did not display it; do not describe it as guaranteed final-answer insertion.
- This repository root is the authoritative npm package and plugin source. The repository marketplace points to `./`; bundled setup stages an immutable copy in the personal marketplace. New tasks load the changed package. Published versions/tags are immutable; runtime changes require a new version.

- GitHub Public Preview is the distribution channel; npm publication is out of scope. Public setup is a dependency-free Node 20+ ESM CLI: `npm test`, `npm run check`, and `npm pack --dry-run --json`. `scripts/public_cli.py` reuses the Python diagnostics. Preserve legacy script behavior.
- For isolated real-Codex setup smoke, set both HOME and CODEX_HOME to temporary workspace directories. Personal marketplace source paths must remain inside HOME; a CODEX_HOME outside HOME requires the `.agents/plugins/claim-verifier/releases` staging fallback. Do not weaken this containment check.
- Setup state records package identity and actual hook/audit completion, never trust. Keep `hook_trust = UNKNOWN`; never write trust files, approval hashes, bypass flags, or simulated UI input. Old running hooks cannot overwrite newer installation identity.
- Verify pinned Python downloads before extracting or executing. Keep upstream notices and update both architecture pins deliberately. npm pack must include the manifest, launcher, Python runtime modules, scripts and defaults, and exclude tests/bytecode/scratch files.
- npm/npx execute the bin through a symlink. Resolve `process.argv[1]` with realpath before comparing it to the ESM entry file; keep a bin-symlink regression and a packed npx smoke.

- Preserve LICENSE and THIRD_PARTY.md in both npm and staged plugin payloads. Release preparation and acceptance evidence live in `docs/changes/github-public-preview/`.
