# Global claim verifier: observable requirements

## Scope
The personal plugin applies to new and existing local Codex projects when enabled and trusted. Project settings can disable the plugin; a plugin-owned project configuration can adjust its level and enforcement. It supports `off`, `receipts`, `verify`, `fresh`, `complete`, and `strict` in increasing order. `report`, `warn`, and `block` are separate enforcement modes.

## User journeys
1. When Codex says tests, build, lint, or typecheck succeeded, the verifier checks a corresponding successful run. With no matching run, the claim is not verified.
2. When Codex claims a file read, write, creation, or deletion, the verifier checks the recorded tool outcome and file state.
3. When Codex claims a commit or push, the verifier checks recorded command results plus local Git state where possible. A remote push requires remote/upstream evidence; a successful `git push` command alone does not prove remote state indefinitely.
4. At `fresh` and above, a check predating a subsequent relevant file change is stale.
5. At `complete` and above, explicit original-task requirements such as running tests or pushing cannot be resolved solely by removing an unsupported final claim. The verifier requests repair through the ordinary Codex flow.
6. An unsupported action the user did not request leads to correction, never automatic execution.
7. When the semantic model is unavailable, clear deterministic claims are still checked. Ambiguous execution claims are inconclusive.
8. After the configured repair budget, the verifier stops requesting repair and asks for truthful disclosure of the remaining gap.

## Rules and edge cases
- `VERIFIED`, `FALSE`, `UNVERIFIED`, `STALE`, and `INCONCLUSIVE` describe evidence, separately from `PASS`, `CORRECT`, `REPAIR`, and `DISCLOSE`.
- Failed commands do not back success claims. Tool error text and model-authored statements are not evidence of success.
- When a shell hook omits exit status, stronger levels require an agent-invoked validation receipt command or other authoritative status source. Running a plain command can leave a claim inconclusive even if its output looks successful.
- Read-only, local validation, local mutation, remote mutation, and high-impact action classifications inform repair wording, without granting permission.
- `strict` uses conservative wording for broad success claims and requires explicit disclosure for inconclusive important claims.
- `report` stores findings; `warn` also surfaces them; `block` requests a continuation within its budget.
- The plugin never sends raw tool output to a semantic model. It sends only the user task and proposed answer for claim normalization.

## Acceptance criteria
- A: `receipts + block` flags `Tests pass` without a test run and allows correction.
- B: `complete + block` requests test execution when the task explicitly requires it, even after the claim is removed.
- C: `fresh + block` flags a test pass that predates a file write.
- D: A false, unrequested push claim requests correction and invokes no push.
- E: A requested push without evidence requests repair and invokes no push itself.
- F: An ambiguous compatibility claim uses Luna normalization when available, but Luna cannot verify it.
- G: Luna failure yields `INCONCLUSIVE`, never `VERIFIED`.
- H: Repair requests stop after the configured budget and the final audit records disclosure needed.

## Open product decision
The user requested final `complete + block` settings, while also recommending a cautious `receipts + report` rollout. The implementation will default to the cautious rollout, then activate the requested final configuration only after hook integration is exercised.
