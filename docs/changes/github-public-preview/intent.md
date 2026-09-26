# Intent — GitHub Public Preview

Publish the existing 0.2.0 release candidate as **Codex Claim Verifier** at
`louis0802/codex-claim-verifier`. Public users need portable source, truthful
installation instructions, clear licensing, and reproducible release assets.

Success means cleaned source on `main`, an immutable `v0.2.0` tag, a GitHub
pre-release with the matching npm-format tarball and SHA-256 checksum, and
documented verification results and platform limitations. npm publication is
excluded. The Git remote must use the requested owner and SSH URL.

Keep the existing verification algorithm and permission boundaries. Never
auto-trust lifecycle hooks or simulate user trust. Manual hook review, trusted
session smoke, and Desktop verification may remain pending for Public Preview;
these must be visible in the README and release notes.

Source: the existing `claim-verifier-source.zip` and `claim-verifier-0.2.0.tgz`.
The 57 archived source files match the release-candidate directory byte for byte.
The original tarball SHA-256 is
`1ccce532cb290f3d58098b59bab0317648030fa6427a131db6eaa544c235c4d0`.
Release preparation will rebuild the asset after public metadata changes.

The user selected MIT, copyright 2026 Louis. The project license and upstream
notices are included in both the npm package and installed plugin payload. Repository existence has been verified:
the requested public repository was empty when inspected. The cleaned source,
annotated tag, pre-release, both assets, and four issues are now published;
[public distribution verification](distribution.md) passed.
