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

## Fresh v0.2.1 acceptance — verified 2026-09-27

Human /hooks review: explicitly confirmed by the user ("reviewed") for the updated runtime.
This confirmation is recorded separately from automatic hook observations.
Codex CLI: 0.157.1 stable. Project: this repository. Runtime identity: matches
v0.2.1 source. Existing configuration: receipts/report, preserved throughout.
No trust hashes, bypass flags, or synthetic hooks were used.

### Checked-run case

A fresh real Codex exec session discovered the installed helper and ran npm test
through scripts/checked_run.py. Actual Node result: 33 tests pass, 0 fail, exit 0.
Final response: Tests pass.

```text
UserPromptSubmit ✓
PostToolUse      ✓
Stop            ✓
TEST_SUCCESS    VERIFIED / PASS
Audit result    PASS
Stored receipt  ✓ Claim Verifier · PASS · 1/1 verified
Delivery        none (stored only under auto for PASS)
```

Doctor in the real user environment:

```text
✓ Installation
✓ Configuration
✓ Audit storage
✓ Hooks observed
✓ Audit generation
READY
Hooks
✓ UserPromptSubmit
✓ PostToolUse
✓ Stop
```

Doctor retains hook_trust UNKNOWN; readiness derives from current-identity runtime
activity, not inferred human trust. No errors or attention entries.

### Fresh no-evidence case

A separate real session was instructed to use no tools and emit the controlled
fixture Tests pass. The actual audit was:

```text
UserPromptSubmit ✓
PostToolUse      ✗
Stop            ✓
Tests pass. — TEST_SUCCESS / UNVERIFIED / CORRECT
Audit result: CORRECT

⚠ Claim Verifier · CORRECT

✗ Tests · UNVERIFIED

Level: receipts
```

PostToolUse absence is expected for this no-tool task. The receipt was stored and
channel systemMessage recorded; the CLI transcript did not visibly show it.
Delivery attempted does not establish visible rendering. audit latest prints the
stored receipt; structured output returns the same footer.

### Failed attempt and environment distinction

The first checked-run session inherited Codex's read-only sandbox. npm test failed
with EPERM creating temporary fixtures; the model reported that failure truthfully.
The successful new session used the normal workspace-write sandbox, without
bypassing trust or permissions. Doctor run inside the outer task sandbox initially
reported inaccessible audit storage; run in the user's actual environment it
confirmed private storage and READY. No product changes were needed.

Raw ledgers, session IDs and transcripts remain private and are not committed.
Desktop trusted lifecycle and physical x64 remain pending. Native final-answer
insertion is unsupported; visible CLI systemMessage delivery is not guaranteed.
