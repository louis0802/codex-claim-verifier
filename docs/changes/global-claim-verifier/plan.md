# Global claim verifier: execution plan

1. **Research — complete.** Inspect current empty workspace, Codex CLI/config, hook contracts, plugin packaging, Luna invocation, and MIT-licensed receipts reference.
2. **Plugin shell — complete.** Create the personal plugin manifest, hook entry points, configuration loader, and plugin-owned data storage. Validate the manifest.
3. **Evidence and claims — complete for supported hooks.** Collect supported tool events, parse clear execution claims, and normalize ambiguous claims through optional Luna. Add an agent-invoked validation receipt because live Bash hooks omit exit status.
4. **Tiered policies — implemented.** Add cumulative levels, independent enforcement, freshness, explicit task intent, risk descriptions, audit output, and repair budget. The Stop continuation remains advisory after budget exhaustion by Codex design.
5. **Verification — complete for supported behavior.** Synthetic tests cover criteria A–H and the plugin validator passes. Live smoke tests in two directories confirmed activation, project override, Stop continuation, and a verified check through the receipt helper.
6. **Global activation — installed, trust pending.** The personal marketplace package is installed. The global rollout setting is `receipts + report` while the user considers the stricter option; exact hooks still require user trust review in `/hooks`.

## Affected paths
Plugin root: `.codex-plugin/plugin.json`, `hooks/hooks.json`, `hooks/*.py`, `claim_verifier/*.py`, `tests/`, and user-facing `README.md`. User config/marketplace are touched only during installation.

## Risks
Partial tool coverage; untrusted hooks skipped; Stop continuation is not a final veto; semantic CLI latency and token cost; command parsing can misidentify work hidden in shell scripts. Mitigate with conservative `INCONCLUSIVE`, no direct repair actions, bounded inputs, and a staged rollout.
