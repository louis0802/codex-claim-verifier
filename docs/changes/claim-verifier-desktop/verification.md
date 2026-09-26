# Verification record

## Environment

- OS: macOS 26.6.2 (25G83)
- Codex CLI: `codex-cli 0.155.0-alpha.2.6`
- ChatGPT desktop app: `26.911.61220` (build `9647`), read from app bundle
- Personal marketplace: `personal`; final plugin listed as installed and enabled at `0.1.0+codex.20260926020308`.
- Verifier setting: `receipts + report` (from the local doctor command)
- Hook trust: **UNKNOWN** from available read-only checks; `/hooks` review is required before interpreting absent activity. The interactive trust step was rejected by automatic approval review because it would persistently enable event-triggered code execution.

## Implementation checks

- `python3 -m unittest discover -s tests -v`: **46 tests passed** in the development copy after adding explicit Desktop observation recording.
- The same **46 tests passed** in the installed package cache (`0.1.0+codex.20260926020308`).
- `validate_plugin.py`: **passed** in the development copy and installed package cache.
- Direct `doctor` and `audit latest` run: **passed** after fixing standalone data-directory discovery. Existing older audits have no heartbeat fields; the commands show hook history as unknown rather than absent.
- Final `doctor` output: package found; plugin installed and enabled; verifier `receipts + report`; hook trust `UNKNOWN`; tagged smoke activity not observed; Desktop hook support and receipt visibility `INCONCLUSIVE`.
- No verifier engine changes (`verify.py`, `claims.py`, `semantic.py`).

## Live smoke matrix

| Capability | Codex CLI directory A | Codex CLI directory B | ChatGPT Desktop |
|---|---|---|---|
| UserPromptSubmit | not observed | not observed | pending |
| PostToolUse | not observed | not observed | pending |
| Stop | not observed | not observed | pending |
| Audit ledger | not observed | not observed | pending |
| checked_run evidence | pending | pending | pending |
| Receipt visible | pending | pending | pending |

`pending` means no live observation has been made. `not observed` means the two read-only CLI tasks finished, but no ledger file appeared for their session IDs. Hook trust could not be verified, so this is not proof that CLI hooks are unsupported.

CLI directory A: a fresh task read `README.md` and reported `python3 -m unittest discover -s tests -v`; no tests ran. Its hashed ledger file was absent. The private task ID is omitted from the public record.

CLI directory B: a fresh task read `README.md` and reported `make test`; no tests ran. Its hashed ledger file was absent. The private task ID is omitted from the public record.

## Desktop classification

- Hook support: **INCONCLUSIVE** pending known fresh desktop task(s)
- Footer presentation: **INCONCLUSIVE** pending live UI inspection
- A tagged prompt identifies a session for correlation; it does not itself identify the launch surface.
- Live Desktop tasks and receipt UI checks remain pending until the hook trust step is approved and reviewed by the user.
