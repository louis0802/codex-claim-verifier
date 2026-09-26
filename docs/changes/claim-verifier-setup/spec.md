# Observable requirements

> Historical setup target. Public Preview currently uses a GitHub release
> tarball; npm registry commands below require future publication. See the
> [public release specification](../github-public-preview/spec.md).

A1. On supported macOS with Node 20+, detect npm, npx, Codex, existing plugin/config and runtime. Preserve working Codex (including Homebrew). Install missing Codex with npm once; report installation failures and successful-install/PATH failures without shell profile edits.
A2. Install the bundled plugin through Codex's personal marketplace. Bundle runtime with the npm package so no development path or unpublished remote source is required. Support explicit package releases via `npx claim-verifier@VERSION setup`, and `--source`/`--plugin-version` for a configured local/Git marketplace. Detect installed/enabled state through Codex JSON listing; preserve installed plugins unless --upgrade is supplied. A disabled or older incompatible plugin needs explicit attention rather than false success.
A3. Create global claim-verifier.toml with requested receipts/report, gpt-6-luna/max, and adaptive/auto footer defaults only when absent. Preserve custom bytes and timestamps. Config schema 1 is reported; no migration is needed for existing optional defaults.
A4. Prepare private runtime storage (directory 0700, JSON/lock files 0600), preferring PLUGIN_DATA and otherwise the documented fallback. Diagnostics must also discover actual Codex plugin data. Store setup state separately from session ledgers.
A5. Setup and doctor never claim human trust from installation. UNKNOWN remains the trust value. Each successful current-package hook produces OBSERVED activity; READY requires all three expected hooks and an actual persisted Stop audit. If current hooks are already observed but the audit is missing, show WAITING FOR AUDIT and ask for a new task without repeating trust instructions. Partial/missing sessions or failed hooks cannot make READY. Changes to the package identity invalidate previous activity; old running packages cannot reactivate a newer setup.
A6. Expose setup, doctor, audit latest, audit list, version. Doctor exits 0 ready, 1 attention/waiting, 2 broken. Missing audit prints a useful message. Version reports CLI, installed plugin, schema. Concise defaults; technical diagnostics with --verbose.
A7. Setup ends with exactly one hook review action (/hooks → Claim Verifier), then a new task. TTY may wait for Enter and launch Codex; non-TTY and --no-launch never launch. --yes skips non-security confirmation including Enter but cannot approve hooks. Ready resumption suppresses unnecessary review guidance.
A8. --dry-run reports planned actions without installs, file creation, chmod, state updates, or launch. --upgrade updates plugin while preserving settings and explains review may recur.
A9. Validate source selectors, versions, paths and manifests. Spawn argument arrays with shell disabled. No eval, unverified executable downloads, trust-file writes or auto-approval. Fail closed with actionable diagnostics and never declare complete after a failed required stage.

Examples: custom `level = "complete"` survives setup unchanged; installed CLI missing from PATH yields failure and npm prefix/PATH diagnostic; all current hooks plus audit observed yields READY on the next doctor/setup.

Product limitations: Node/npm entry prerequisite; platform macOS only; account sign-in belongs to Codex; publication is a release step. No consequential product decision prevents local implementation.
