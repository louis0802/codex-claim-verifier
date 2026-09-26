# Plan — GitHub Public Preview

1. Inspect the source archive, existing code, guidance, metadata, diagnostics,
   tests, notices, and existing verification. **Complete:** source copy matches
   the archive; LICENSE, public metadata, and repo marketplace are absent.
2. Resolve license; clean public documentation and metadata; add `.gitignore`
   and marketplace catalog; preserve provenance. **Complete:** MIT selected,
   real historical IDs removed, public help/error guidance corrected, notices
   retained in installed payloads with matching Node/Python identity.
3. Audit all files for local references, sensitive data, generated/private files,
   and notice obligations; write `release-prep.md` (A1–A4). **Complete.**
4. Run Python/Node/syntax/plugin checks, actual marketplace install, package
   assertions, and isolated packed setup/idempotency/doctor/version smoke (A3,A5). **Complete:** 86 tests plus actual local npx/Codex
   and root marketplace checks; no trust changes.
5. Finish README with a validated GitHub installation flow; synchronize evidence
   and release notes, pack the final source, hash the asset (A1–A5). **Complete:** 31 package files, final source match,
   retained notices, checksum and release notes ready.
6. Initialize/stage/review Git, check whitespace, commit the exact requested
   message, configure exact remote, push main, compare HEAD, tag and push (A6).
7. Publish GitHub pre-release, tarball/checksum, metadata/topics, and four platform
   tracking issues (A7). Authenticated access is a dependency.
8. Test installation from the public asset and verify its hash against the local
   release. Report manual trust/live claim/READY acceptance as pending (A8).

Keep the original workspaces unchanged. Test files, logs, npm caches, and isolated
Codex installations stay outside the public repository. Keep packaging files
required by the plugin. Optional CI may be deferred to avoid expanding release
scope. The license decision gates publication; failed checks gate commit/push.
