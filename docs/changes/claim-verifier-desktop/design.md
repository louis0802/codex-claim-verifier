# Design

## Existing system

`hooks/hooks.json` invokes `hooks/claim_verifier.py`, which calls `claim_verifier.hook.handle`. `store.ledger` holds private per-session JSON. `collector` supplies evidence and `verify` decides claim status. The current renderer stores receipts in Stop audits; UI display of `systemMessage` is unproven.

## Diagnostics data flow

Record a bounded `runtime` object in the same locked, atomic session ledger before normal hook processing. It includes first/last seen UTC timestamps, sanitized cwd (home abbreviated, control characters removed), booleans for `PLUGIN_ROOT`, `PLUGIN_DATA`, `session_id`, `turn_id`, and `cwd`, ordered unique hook stages, a bounded recent heartbeat list, and optional `desktop-smoke` tag. On Stop, set that heartbeat's `audit_created` only after appending the audit. Use a reserved diagnostic session key if a hook lacks `session_id`, while retaining the existing inconclusive hook response.

Do not copy prompts, tool inputs, tool outputs, or environment values into runtime diagnostics. Existing prompt/evidence fields are unchanged. Keep ledger mode `0600`. Cap heartbeats to prevent unbounded growth.

## Reader commands

`claim_verifier.diagnostics` enumerates session ledgers, safely ignores malformed/unrelated files, selects the latest by diagnostic/audit timestamp, and builds a JSON-capable status object. `scripts/doctor.py` and `scripts/audit.py` are thin, read-only command adapters. A default doctor view shows recent general activity and the latest tagged smoke session if present. It reports unknown trust and receipt visibility unless live evidence was recorded separately. `audit latest` chooses the latest audited session, not the latest prompt-only session.

The status object describes observed stages and gaps; it does not call a tagged task "desktop" without external launch provenance. Full/partial/no observed hook classification is applied in `verification.md` to live tasks of known origin. The marker is only a correlation aid.

An explicit `scripts/record_desktop.py` command stores a `0600` observation file beside the ledgers. It accepts a tagged session ID that exists in the ledger plus a receipt-visibility enum chosen after UI inspection. The record labels the surface origin as operator supplied. Doctor joins those session IDs to machine-recorded hook stages and checked-run evidence, and reports `FULL` only when all three hooks, a Stop audit, and verified checked-run evidence have been observed across the recorded Desktop tasks. The observation file cannot manufacture hook or audit evidence. With no operator record, Desktop remains `INCONCLUSIVE`.

## Failure handling

Diagnostic writes use existing ledger locking. Reader failure on an individual corrupt file does not hide valid sessions. If a hook cannot write the ledger, its existing fail-closed warning path remains. No changes to `verify.py`, `claims.py`, or `semantic.py` are planned.

## Rollout

Develop and test in this deliverable copy. Validate the manifest, then sync the tested files to the personal-marketplace source, update the cachebuster with the plugin-creator helper, and reinstall. Fresh tasks are required to load the new hook package. Record CLI/desktop runtime behavior separately after installation.
