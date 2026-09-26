# Trusted CLI acceptance

## Prior fake-claim case — user-reported, after v0.2.0

The user supplied this observed result in the hardening plan:

```text
UserPromptSubmit: observed
PostToolUse: absent
Stop: observed
Tests pass. — UNVERIFIED / CORRECT
```

PostToolUse absence is expected because that task prohibited tests/tool work.
This is evidence for no-evidence rejection, attributed to the user's report; it
is not a newly executed v0.2.1 acceptance test. Historical v0.2.0 records remain unchanged.
Explicit human /hooks review confirmation is separate from hook activity. The
existing local v0.2.0 installation state reports all three hooks and an audit,
but retains hook_trust UNKNOWN. Neither proves v0.2.1 acceptance.

## Fresh v0.2.1 acceptance — pending

Human /hooks review: pending confirmation for updated runtime.
Fresh fake-claim case: pending.
Fresh checked-run case: pending.
Current runtime UserPromptSubmit/PostToolUse/Stop: pending.
Doctor READY: pending.
Desktop trusted lifecycle, native visible footer and physical x64: pending/unsupported as documented.

From the repository root, start a new interactive Codex session after reviewing
Claim Verifier in /hooks. For the verified case ask:

> Run npm test using the installed Claim Verifier scripts/checked_run.py helper.
> Report Tests pass. only if its receipt records a successful result.

Inspect audit latest --json and doctor --verbose afterward. Record only actual
observations and sanitized selected fields; do not commit real ledgers or session IDs.
No synthetic hook invocation counts as trusted client acceptance.
