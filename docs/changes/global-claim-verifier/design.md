# Global claim verifier: design

## Runtime mapping
Codex loads `hooks/hooks.json` from the personal plugin. `UserPromptSubmit` records a turn's user prompt. `PostToolUse` records supported local tool input/output. `Stop` reads the latest assistant message, normalizes claims, verifies against the evidence ledger, writes an audit record, and optionally returns `decision: block` with a bounded continuation reason. These are the documented hook inputs and outputs. Plugin `PLUGIN_DATA` holds per-session ledgers outside repositories.

## Components and data
- `config`: global defaults from a plugin-owned TOML file under the user's Codex directory and optional `.codex/claim-verifier.toml` project override. Project overrides are read only for paths marked trusted in Codex user configuration. Invalid configuration emits a hook warning and performs no verification for that event; it never claims a pass. Codex's own `[plugins."claim-verifier@personal"].enabled` controls plugin activation in a trusted project.
- `collector`: reduces tool payloads to bounded summaries, command text, exit status when available, file paths, and Git action type. It never accepts assistant prose as execution proof. Live Codex CLI `Bash` hooks provide model-facing stdout but omit process exit status, as measured in two smoke tasks.
- `scripts/checked_run.py`: an optional, agent-invoked validation command for tests, builds, lint, and typecheck. It runs only allowlisted local validation commands through the normal Codex shell tool and prints a structured exit-status receipt. The hook never invokes it; `PostToolUse` validates its exact command path, arguments, and receipt before treating the status as evidence. Plain shell checks without an exposed status remain `INCONCLUSIVE` at `verify` and above.
- `store`: one JSON ledger per session, with atomic replacement and file locking. Events include time, turn id, tool id, cwd, command, exit status, and changed paths. Retain only bounded result excerpts, redact common secret patterns, and keep mode `0600`.
- `claims`: deterministic patterns first; only unresolved agentive execution statements reach the semantic adapter. The adapter invokes an isolated `codex exec` session with `gpt-6-luna`, `max`, hooks disabled, read-only sandbox, and JSON output schema. Failure yields `INCONCLUSIVE`.
- `verify`: policy tiers select proof strength. For `verify`, commands require explicit successful exit status. For `fresh`, later writes invalidate state-dependent checks. Commit and push checks use the recorded command and read-only Git queries where available.
- `intent`: conservative explicit task extraction for tests/build/lint/typecheck/commit/push. No semantic model may authorize or execute repairs.
- `decision`: combines claim status with task requirement. Block-mode `Stop` requests `CORRECT` or `REPAIR` until the per-turn budget is exhausted; thereafter it requests disclosure in the audit and warning.

## Trust and limitations
Hook events are a useful observation channel, not a complete reference monitor: hosted tools and specialized paths can bypass `PostToolUse`. A hook must not mark a claim verified solely from an unobserved tool. `Stop` creates a continuation prompt rather than rejecting the final answer; a live one-retry smoke task repeated the unsupported claim after the retry. Bounded retries imply a truthful-disclosure request cannot be guaranteed. The plugin should describe itself as a guardrail, not an absolute proof system.

## Installation and rollback
Stage the source in this deliverable directory. Add it to the personal marketplace, install using Codex plugin facilities, review/trust the hook definition, and exercise it in fresh local tasks in two directories. Remove or disable the plugin to roll back; audit files remain in plugin data until removed by the user.

## Sources
- [Codex hooks](https://learn.chatgpt.com/docs/hooks)
- [Plugin packaging and personal marketplaces](https://developers.openai.com/plugins/build/plugins)
- [GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna)
- [Claude Code receipts reference](https://www.npmjs.com/package/%40sudhanshu1402/receipts)
