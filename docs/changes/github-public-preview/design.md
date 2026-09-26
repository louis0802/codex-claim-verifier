# Design — GitHub Public Preview

Keep the existing root package layout: dependency-free Node ESM CLI in `cli/`,
Python verifier in `claim_verifier/`, lifecycle definitions in `hooks/`, public
and legacy helpers in `scripts/`, and tests/documentation beside them. No
verification behavior changes are planned. Public CLI help/error guidance points
to GitHub tarballs rather than an unpublished npm registry command.

Update package and plugin metadata to 0.2.0 and public repository identity. Add
the chosen license and exclusions. Use the Plugin Creator's existing marketplace
shape and validator. The catalog will reference the root plugin rather than
duplicate runtime sources under `plugins/`; validate this relative root with the
real Codex marketplace tooling before accepting it. This is a layout deviation
from the scaffold's `./plugins/claim-verifier` convention, retaining one source
of truth for npm packaging and plugin identity.

Build `claim-verifier-0.2.0.tgz` from the final source with `npm pack`; retain it
outside the repository. Use the GitHub release tarball URL for distribution if
the post-release smoke passes. Document installation into a private test prefix
for verification and a user prefix for Quick Start. The CLI version and installed
plugin manifest must both report 0.2.0. Do not suggest an unpublished npm registry
package. Retain LICENSE and THIRD_PARTY.md in the immutable installed payload; include
them in payload identity. A regression verifies that both survive staging.

Audit the entire release source and npm payload, manually classifying broad
secret-pattern hits as implementation, synthetic fixtures, or actual sensitive
data. Never inspect or copy the user's live plugin ledgers into the repository.
Historical docs keep only portable, nonsensitive technical evidence.

Tests and real Codex setup run in isolated test home/config/cache directories.
The test harness may set child-process HOME and CODEX_HOME for isolation, but
does not repurpose the host shell's variables. No trust records are written.
Hook simulation remains distinct from live trust verification.

After all release gates pass, initialize Git, stage and inspect every public file,
run whitespace checks, make the user-requested initial commit, configure the exact
remote, and push. Compare remote main with local HEAD before annotating and
pushing the tag. Create the GitHub pre-release and four issues using authenticated
tools if available. Public source and asset downloads must match local evidence.
Any defect found after publication uses a new patch release; never rewrite the
published tag. No npm publication or CI trust interaction is permitted.
