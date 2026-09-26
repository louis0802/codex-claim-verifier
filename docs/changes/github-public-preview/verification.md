# Verification — v0.2.0 Public Preview

## Automated and local release gates

Host: macOS arm64; Node 24.13.1; Python 3.11.5;
actual Codex CLI 0.158.0-alpha.2.1. Tests ran against the cleaned source copy.

| Check | Result | Acceptance |
| --- | --- | --- |
| Python unittest discovery | 59 passed | A5 |
| Node CLI tests | 27 passed; total 86 automated tests | A2,A5 |
| Node syntax checks | All CLI modules and hook launcher passed | A5 |
| Plugin Creator validator | Passed | A3,A5 |
| Marketplace name reader | codex-claim-verifier accepted | A3 |
| Real local repository marketplace | Codex added catalog, installed root plugin 0.2.0, preserved config | A3,A5 |
| npm pack dry run and real payload inspection | 31 files; required assets present; no tests, docs, bytecode, private state, nested archives, or dependencies | A1,A2,A5 |
| Package-source comparison | Every tarball file equals the matching final source file | A1,A5 |
| Real offline packed npx/Codex setup | Setup and repeat succeeded; config bytes/mtime preserved; CLI and plugin 0.2.0; notices retained | A2,A5 |
| Real packed doctor/audit/dry-run | Doctor exit 1 at WAITING FOR HOOK REVIEW; empty audit commands work; no synthetic READY asserted | A4,A5 |
| Source audit | Broad matches reviewed; no secrets, workstation links, runtime ledgers, or real task IDs | A1 |
| Initial staged whitespace/content review | Complete 66-file public source reviewed; git diff --check and cached diff check passed; no private/generated files | A6 |

The first license-staging change exposed a Node/Python identity mismatch in the
existing regression. Both implementations now include available notices in
identity, supporting legacy payloads without them. The full suites passed after
the correction. No checks were removed or weakened. One regression was added for
retaining the notices in a staged installation.

Core `verify.py`, `claims.py`, `collector.py`, `semantic.py`, `footer.py`, and hook
decisions are unchanged from the release candidate. Runtime edits affect notice
staging/identity and GitHub-only diagnostic wording.

## Distribution and live acceptance

Public transport is tested after GitHub publication; the tagged source cannot
record a completed post-publication result in advance. The [public distribution record](distribution.md) now contains exact tag/asset
hashes and the successful actual HTTPS and pinned Git marketplace results. The v0.2.0 tag and asset will not be rewritten.

Manual `/hooks` review, a fresh trusted fake claim (`TEST_SUCCESS / UNVERIFIED /
CORRECT`), a successful checked-run claim (`TEST_SUCCESS / VERIFIED / PASS`), and
trusted-session doctor READY remain pending. Unit tests and direct synthetic
launcher tests establish logic but do not establish human trust or client delivery.
Live trusted Desktop behavior/footer visibility and physical macOS x64 execution
also remain pending. npm was not published.

Self-review checked the acceptance criteria, package contents, ignored artifacts,
notice retention, source comparisons, preserved configuration, and truthful trust
limits. No independent agent review was requested.

## Final asset

`claim-verifier-0.2.0.tgz` contains 31 files matching the source. SHA-256:

```text
e3c80d124226bd5d5626d7bdf62a041194148a159e26fe6aee3a98c0e5c93c34
```

The exact final asset passed the actual isolated npx/Codex and root-marketplace
smoke again after the final README update. Existing configuration bytes and mtime
were preserved. No production trust or runtime state was changed.
