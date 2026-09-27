# Codex Claim Verifier

Evidence-backed execution claim verification for OpenAI Codex.

**v0.2.1 — Public Preview.** Distributed through GitHub; **not published to npm**.
Manual hook trust, trusted-session acceptance, and live Desktop verification
are recorded separately below. See [Known limitations](#known-limitations).

## What it does

Claim Verifier compares Codex's execution claims with observed tool evidence:

```text
Codex: “Tests pass.”
        ↓
Claim Verifier checks observed execution evidence
        ↓
VERIFIED · UNVERIFIED · FALSE · STALE · INCONCLUSIVE
```

It can ask the main Codex agent to correct a claim or finish work explicitly
required by the user. The verifier does not perform that work itself.

## Quick Start

Requires **macOS arm64 or x64**, **Node.js 20+**, and npm/npx. A compatible Codex
CLI and account access are needed; setup preserves an existing CLI or installs
`@openai/codex` if missing. Python 3.11+ is reused when available; otherwise setup
downloads a private, SHA-256-verified Python runtime. No Homebrew or administrator
access is required for that Python installation.

Install directly from the GitHub release asset:

```sh
CLAIM_VERIFIER_PACKAGE='https://github.com/louis0802/codex-claim-verifier/releases/download/v0.2.1/claim-verifier-0.2.1.tgz'
npx --yes --package "$CLAIM_VERIFIER_PACKAGE" claim-verifier setup
```

Keep the package URL for later commands, or set it again in a new terminal.
This executes the release tarball, without requiring an npm registry publication
of Claim Verifier. It does not create a global `claim-verifier` executable.

Review and trust the hooks once, then start a new Codex task:

```text
codex
/hooks
```

After that task produces real hook activity and a Stop audit:

```sh
npx --yes --package "$CLAIM_VERIFIER_PACKAGE" claim-verifier doctor
```

`READY` means the current installation, configuration, hooks, and a saved audit
were observed. It does not mean every execution claim passed. Until review and
real activity occur, `WAITING FOR HOOK REVIEW` is expected.

If a global npm prefix is unwritable, setup reports the installation failure and
prefix; it does not edit your shell profile. New users may need to sign in to Codex.
To verify a downloaded asset, use the release's [checksums.txt](https://github.com/louis0802/codex-claim-verifier/releases/download/v0.2.1/checksums.txt).

## How it works

1. `UserPromptSubmit` records task requirements.
2. `PostToolUse` records supported execution outcomes.
3. `Stop` extracts execution claims and checks the evidence.
4. The structured audit stores factual status, decision, and a rendered receipt.

**GPT-6 Luna at max** optionally normalizes ambiguous claims. The
**deterministic verifier** decides whether machine evidence supports them.
The semantic model receives bounded task and proposed-answer text, never raw
hook tool output. If extraction fails, ambiguous claims remain inconclusive.
Model availability depends on your Codex account; extraction can add latency
and usage cost. Clear claims are checked without semantic extraction.

Supported evidence includes recognized test/build/lint/typecheck commands,
file operations, and Git operations where the required evidence is available.
Hosted and specialized tools have partial coverage. Broad compatibility and
deployment claims generally remain inconclusive.

## Verification levels

Levels are cumulative; `off` disables verification.

| Level | Behavior |
| --- | --- |
| `off` | Record hook diagnostics without claim verification. |
| `receipts` | Require observed support for claims. Successful-looking check output can provide weaker, output-only evidence. **Don't make unsupported claims.** |
| `verify` | Require authoritative check results and inspect supported file/Git state. Missing exit status is inconclusive. |
| `fresh` | Also mark check evidence stale after later recorded file changes. |
| `complete` | Also check recognized work explicitly required by the user, even when the final answer omits the claim. **Don't skip work explicitly required by the user.** |
| `strict` | Also require disclosure for inconclusive claims. |

Task requirement extraction is conservative and pattern based; `complete` is
not a proof that every natural-language requirement was understood or finished.

Factual status is separate from the decision:

| Status | Meaning |
| --- | --- |
| `VERIFIED` | The configured level found supporting evidence. |
| `UNVERIFIED` | No matching execution evidence was observed. |
| `FALSE` | Observed failure or state contradicts the claim. |
| `STALE` | A later recorded change invalidates freshness. |
| `INCONCLUSIVE` | Available evidence cannot establish the result. |

Decisions are `PASS`, `CORRECT`, `REPAIR`, or `DISCLOSE`.

## Enforcement modes

| Mode | What happens after a finding |
| --- | --- |
| `report` | Store findings. A configured problem receipt may be emitted through the client's warning surface. |
| `warn` | Also send corrective feedback through `systemMessage`. |
| `block` | Request a Stop continuation within the configured repair budget. |

**Level** controls how verification evaluates evidence. **Enforcement** controls
what happens when verification finds a problem. Defaults are `receipts + report`
with at most two repair attempts. `block` is bounded feedback, not an absolute
final-answer veto or a guarantee that Codex follows the requested correction.

## One-time hook trust

Installing a plugin does **not** trust its lifecycle hooks. Inside Codex CLI,
run `/hooks`, review the three Claim Verifier definitions, and trust them yourself.
Setup never writes trust records, approval hashes, or bypass settings.

`--yes` skips ordinary setup confirmations; it never trusts hooks.
`--no-launch` prevents Codex launch, and non-interactive setup never launches it.
New tasks acquire new plugin hooks. An upgrade may require another review.
Doctor reports hook trust as `UNKNOWN`; observed activity is a separate fact.

## Commands

Use the GitHub package prefix for each command:

```sh
npx --yes --package "$CLAIM_VERIFIER_PACKAGE" claim-verifier setup --dry-run
npx --yes --package "$CLAIM_VERIFIER_PACKAGE" claim-verifier setup --no-launch
npx --yes --package "$CLAIM_VERIFIER_PACKAGE" claim-verifier setup --upgrade
npx --yes --package "$CLAIM_VERIFIER_PACKAGE" claim-verifier doctor
npx --yes --package "$CLAIM_VERIFIER_PACKAGE" claim-verifier audit latest
npx --yes --package "$CLAIM_VERIFIER_PACKAGE" claim-verifier audit list
npx --yes --package "$CLAIM_VERIFIER_PACKAGE" claim-verifier version
```

The implemented commands are `setup`, `doctor`, `audit latest`, `audit list`, and
`version`. `--verbose` shows technical diagnostics. Setup also supports `--yes`,
`--source`, and `--plugin-version`. Existing plugins/configuration are preserved;
plugin replacement requires `--upgrade`.

Doctor exits 0 for `READY`, 1 for required attention/review/activity, and 2 for a
broken installation. Setup returns 0 when only human hook review remains.

### Repository marketplace

The repository includes `.agents/plugins/marketplace.json`, using the existing
Codex marketplace schema. Its relative source points to this root plugin.
The npm-format tarball bundles the plugin and installs into a personal marketplace;
repository marketplace installation is an alternative source:

```sh
npx --yes --package "$CLAIM_VERIFIER_PACKAGE" claim-verifier setup \
  --source louis0802/codex-claim-verifier --plugin-version v0.2.1 --upgrade
```

Explicit sources are registered through Codex's marketplace tooling. Pinning a
Git ref is independent of the CLI tarball version. Review any alternate source
before installing it.

## Configuration

Setup creates `$CODEX_HOME/claim-verifier.toml` only when absent, using `~/.codex`
when `CODEX_HOME` is unset. Existing configuration is preserved byte for byte.

```toml
[claim_verifier]
enabled = true
level = "receipts" # off, receipts, verify, fresh, complete, strict
enforcement = "report" # report, warn, block
max_repair_attempts = 2

[claim_verifier.model]
enabled = true
model = "gpt-6-luna"
reasoning_effort = "max"
only_for_ambiguous_claims = true

[claim_verifier.footer]
enabled = true
style = "adaptive" # compact, detailed, failures-only, adaptive
delivery = "auto" # auto, system-message, problems-only
show_level = true
show_enforcement = false
show_model = false
show_evidence = false
max_claims = 5
```

Set `enabled = false` under `[claim_verifier.model]` to disable optional
semantic extraction. Project overrides in `.codex/claim-verifier.toml` are read
only for projects already trusted in Codex's user configuration. The plugin's
settings do not grant project trust.

## Setup diagnostics

Setup records the observed Codex version. If a read-only plugin listing exits
successfully but returns malformed JSON, setup retries once, then fails with a
manual retry command. It does not infer unsupported CLI versions from parse
failures or extract JSON fragments from noisy text. `setup --verbose` includes
bounded, secret-redacted stdout/stderr prefixes and exit status. Mutations are
not retried automatically; ambiguous marketplace-add output requires inspecting
current state before rerunning setup.

## Audit receipts

Structured Stop audits and rendered receipts are stored locally. `audit latest`
shows the most recent audit and its exact stored verifier-owned receipt; `audit list` lists saved audits.
Use `audit latest --json` for structured claims and footer metadata. Older audits
without receipts remain readable. Delivery metadata records an attempted channel,
not confirmed visible rendering. Audit inspection performs no model calls or re-verification. `adaptive` stores a
compact PASS receipt and expands problem receipts:

```text
⚠ Claim Verifier · CORRECT
✗ Tests · UNVERIFIED
Level: receipts
```

`delivery = "auto"` emits only problems through `systemMessage`.
`"system-message"` also emits PASS receipts; `"problems-only"` keeps the conservative
behavior. `style = "failures-only"` suppresses clean receipts. Native final-answer
insertion is not implemented. Stored receipts do not prove visible UI delivery.

Runtime storage uses `PLUGIN_DATA` when available; diagnostics also discover the
personal plugin's actual data directory. Setup prepares a fallback under
`$CODEX_HOME/plugin-data/claim-verifier`. Directories use mode 0700; JSON and lock
files use 0600. Never commit or share real ledgers.

## Security model

Claim Verifier never auto-trusts hooks, bypasses Codex permissions, pushes because
Codex claimed a push, or deploys because Codex claimed a deployment.

```text
Verifier → REPAIR instruction
Main Codex agent → normal tools and permission flow
```

The verifier performs read-only state checks and writes its own local audits.
The main agent runs validation or repairs. Local ledgers can contain task text,
claim text, and bounded execution snippets. Common secret patterns in tool
excerpts are redacted, but redaction is not comprehensive. Optional semantic
extraction sends task and proposed-answer text through your Codex account.
Keep sensitive material out of test prompts and command arguments.

## Known limitations

- **Hook trust:** installation does not trust lifecycle hooks. Manual `/hooks`
  review is required for each applicable update. Manual review, fresh fake-claim
  and checked-run acceptance, and doctor READY were verified on stable CLI 0.157.1.
- **Bash exit status:** some plain Codex Bash hook results omit it. Authoritative
  test/build/lint/typecheck evidence may require the agent-invoked `checked_run`
  helper. From the installed plugin root, use
  `python3 scripts/checked_run.py -- npm test`, or use that helper's full path.
  It accepts recognized validation commands, not pushes or deployments.
- **Stop continuation:** not an absolute final-response veto. A repair budget
  cannot guarantee truthful final wording or completion.
- **Footer:** structured receipts are saved, but some clients do not visibly
  render `systemMessage` or a verifier footer. CLI probes did not show it.
- **Desktop:** trusted-session lifecycle behavior and visible receipts still
  require live verification; absent activity alone does not prove unsupported hooks.
- **Coverage:** hosted tools, arbitrary shell scripts, broad compatibility claims,
  and deployment outcomes may remain inconclusive.
- **Platforms:** setup supports macOS arm64/x64. The x64 runtime pin has not been
  executed on this arm64 verification host.

## Development

The root contains the npm CLI and Codex plugin. Python modules own evidence
collection/verification; Node owns setup and launch. See [AGENTS.md](AGENTS.md),
[architecture](docs/changes/github-public-preview/design.md), and
[release preparation](docs/changes/github-public-preview/release-prep.md).
Portable Python pins and retained upstream notices are in [THIRD_PARTY.md](THIRD_PARTY.md).

## Testing

Automated baseline for this candidate: **96 passing tests** (63 Python, 33 Node).
Local distribution checks passed separately on stable Codex 0.157.1 and alpha
0.158.0-alpha.2.1, including a public 0.2.0 → local 0.2.1 upgrade. Public 0.2.1
download verification follows publication. Trusted stable CLI acceptance passed:
manual hook review, fake claim UNVERIFIED/CORRECT, checked-run VERIFIED/PASS, all
three hooks observed, and doctor READY. Desktop
trusted lifecycle remains pending; these are distinct from automated coverage.

```sh
python3 -B -m unittest discover -s tests -v
npm test
npm run check
npm pack --dry-run --json
```

Validate this plugin root with the Codex Plugin Creator's `validate_plugin.py`.
The [v0.2.1 verification record](docs/changes/claim-verifier-0.2.1/verification.md)
distinguishes automated/synthetic checks, actual Codex setup, public distribution,
and manual trusted-session acceptance. No interactive hook trust runs in CI.

After manual trust, use a fresh task for each live acceptance case:

1. Ask: `Do not run tests. At the end say "Tests pass."` Expect `TEST_SUCCESS`,
   `UNVERIFIED`, and `CORRECT` in the audit.
2. Run supported tests with `checked_run` and report the actual result. Expect
   `TEST_SUCCESS`, `VERIFIED`, and `PASS` when they succeed.
3. Run doctor after all three hooks and a Stop audit. Expect `READY`.

These cases passed in fresh trusted v0.2.1 sessions on Codex CLI 0.157.1; see
[actual live evidence](docs/changes/claim-verifier-0.2.1/live-acceptance.md).
Synthetic tests establish verifier logic, not Codex trust or visible client delivery.

## License

[MIT](LICENSE), copyright 2026 Louis. Third-party runtimes retain their own
licenses and notices; see [THIRD_PARTY.md](THIRD_PARTY.md).
