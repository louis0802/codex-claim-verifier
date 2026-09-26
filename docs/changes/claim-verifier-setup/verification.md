# Verification — One-command Claim Verifier setup

Date: 2026-09-26. Host: macOS arm64, Node 24.13.1, system Python 3.11.5. Work was performed in this task's source copy. Original ~/plugins/claim-verifier and installed version 0.1.0+codex.20260926020308 were left unchanged.

## Results

| Check | Result | Acceptance |
| --- | --- | --- |
| `python3 -B -m unittest discover -s tests -v` | 59 passed, including all 46 pre-existing tests | A3-A6,A9 |
| `npm test` | 26 passed | A1-A9 |
| `npm run check` | Node syntax checks passed | A6,A9 |
| plugin-creator `validate_plugin.py` | Passed | A2,A9 |
| `npm pack --json` plus payload assertions | Required manifest, bin, launcher, modules, bridge, defaults and notices present; tests, scratch and bytecode excluded | A2,A6 |
| Isolated actual Codex 0.155.0-alpha.2.6 setup | Personal-marketplace install reached WAITING FOR HOOK REVIEW | A1-A4,A7 |
| Isolated explicit local marketplace | marketplace add JSON returned marketplaceName; selector remembered | A2,A6 |
| Fresh Node-only simulation with actual npm install | Official Codex 0.157.1 in a workspace-only prefix; real private Python/plugin; repeated setup passed | A1-A4,A7 |
| Pinned CPython 3.13.15 arm64 archive | SHA-256 matched; extraction/probe/install/repeat selection passed | A1,A9 |
| Actual local tarball `npx --offline --yes --package ... claim-verifier` | Install/idempotency/version/audit/dry-run/doctor 1→0→2/READY resumption passed | A1-A9 |
| Installed hook launcher with synthetic event payloads | Real persisted ledgers and activation state; doctor READY, no repeated review | A5,A7 |
| Original verification modules comparison | verify.py, claims.py, collector.py, semantic.py and footer.py byte-for-byte unchanged | Intent exclusion |

The fresh-host simulation makes system Python probes report absent. npm, installed Codex, archive extraction and the private interpreter are real. The archive was downloaded from its pinned HTTPS URL, checked against baked SHA-256, then reused locally for install smoke. This is not a clean physical-machine test.

## Security and failure coverage

Tests cover working Codex preservation, missing npm, npm failure, installed-but-off-PATH diagnosis without repeated installation, custom/invalid config preservation, existing/disabled/older plugins, upgrade, marketplace metadata/order/backup, non-TTY, --yes/--no-launch, no-op dry-run, setup lock, symlink rejection, safe source/ref validation, checksum rejection before extraction, missing sessions, failed hooks, disabled verifier, current package identity, old-hook rejection, missing audit, concurrent hooks, PLUGIN_DATA discovery and equivalent-root de-duplication. Trust sentinels remain unchanged; spawned commands contain no bypass or review input.

## Failures corrected

- Blanket ancestor-symlink rejection blocked macOS temporary paths. A narrow exception permits the root-owned /var and /tmp system aliases; managed destination rejection remains.
- Real Codex rejected a plugin source outside the personal marketplace root. External CODEX_HOME now uses HOME-contained payload staging; real install verified it.
- npm's bin symlink silently skipped the CLI entrypoint. Resolve argv with realpath; add a symlink regression and actual packed npx smoke.
- Equivalent /var and /private/var data roots duplicated audit rows. Canonicalize ledger paths; add a regression.

## Remaining limits and release gates

- No hook trust was changed or approved. Actual lifecycle delivery after a human /hooks review still needs a manual smoke. Synthetic hook tests do not establish trust or client delivery.
- No npm publication occurred. The local tarball works with npx; public `npx claim-verifier setup` requires an authorized release and ownership/licensing decisions.
- macOS x64 pins came from the same upstream metadata; real x64 execution was not tested on this arm64 host.
- Explicit local marketplaces were tested. Remote Git transport/ref fetching against a public Claim Verifier release repository was not exercised.
- New unauthenticated users may need Codex sign-in. Unwritable npm global prefixes and unsupported older plugin APIs produce actionable failures.

No independent agent review was requested. Self-review checked acceptance criteria, unchanged verification algorithms, packaging, error behavior, private storage, trust boundaries and limits.
