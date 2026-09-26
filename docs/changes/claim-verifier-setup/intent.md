# One-command Claim Verifier setup

> Historical setup target. Public Preview currently uses a GitHub release
> tarball; npm registry commands below require future publication. See the
> [public release specification](../github-public-preview/spec.md).

Give new macOS users a public npm command that installs the existing verifier, prepares global settings and private storage, exposes diagnostics and audits, and stops at Codex's human hook review. Existing users must keep their working Codex installation and custom configuration.

Success: `npx claim-verifier setup` reaches WAITING FOR HOOK REVIEW; after actual current-package prompt, tool, and Stop activity with a persisted audit it reaches READY automatically. Repeated setup is safe. CLI diagnostics are useful in scripts.

Constraints: Node 20+ is the entry prerequisite; support arm64/x64 macOS. Existing Python runtime needs 3.11+, so bootstrap a pinned, SHA-256 verified portable Python when absent. Honor CODEX_HOME and PLUGIN_DATA. Never change hook trust, execute bypass flags, simulate approval, or redesign verification decisions. No publishing, live installation upgrade, or recurring jobs is authorized by this implementation request.

Exclusions: uninstall/config editing commands, forced migrations, non-macOS setup, and user authentication automation. Codex account sign-in can still be necessary on an unauthenticated machine; the tool cannot promise to bypass that independent product requirement. Public npm availability requires a later authorized release.
