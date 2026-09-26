# Release-preparation report — v0.2.0

## Package structure

The repository root is both the npm-format package and Codex plugin. `cli/`
contains dependency-free Node 20+ setup/diagnostics; `claim_verifier/` contains
Python 3.11+ evidence logic; `hooks/` defines and launches three lifecycle hooks;
`scripts/` contains public bridges, legacy diagnostics, and checked-run support.
Tests, historical change records, and this release's four documents remain in
the public source. Runtime state and release assets remain outside it.

The source archive's 57 files matched the candidate directory. The package stays
named `claim-verifier`, version 0.2.0; the repository/title use
`codex-claim-verifier` / **Codex Claim Verifier**. The repository catalog points
to the root plugin, avoiding duplicate runtime trees.

## Public-safe files and sensitive-data audit

The complete tree was reviewed, including hidden plugin metadata, all code,
tests, docs, package metadata, and Python download pins. No user credentials,
environment dumps, cookies, real prompts/history, private URLs, or runtime
ledgers are included. Runtime filenames and session field names in implementation
are necessary public code, not saved runtime data.

Broad API-key/token/password/secret/authorization/bearer/session scans were
reviewed manually. Matches are redaction logic, configuration/parser field names,
synthetic fixtures, or explanatory text. The fake credential URL at example.com
tests source rejection; fake secrets test redaction. Two real historical task IDs
were removed. No real UUID/session IDs remain in the public tree.

Focused scans found no workstation paths, private build links, private-key
material, or GitHub/OpenAI credential-shaped values. Existing paths are portable
user configuration conventions, runtime-generated paths, or temporary-directory
test/platform examples. No original workstation links needed replacement; newly
written documentation uses repository-relative links.

`.gitignore` excludes dependency/build/cache outputs, logs, environment files,
runtime ledgers, temporary/backup files, source archives, and tarballs. Required
plugin metadata, modules, helpers, defaults, license, and notices stay included.

## Metadata, license, and notices

Added MIT LICENSE, copyright 2026 Louis, as explicitly selected by the user.
Package, plugin, README, and notices agree. Public owner/repository/homepage/issues
URLs are consistent. Plugin version is now 0.2.0 rather than a local cachebuster;
publisher/title are public values.

The original design record states an independent implementation using the
MIT-licensed Claude receipts project as a design reference; its attribution is
retained in THIRD_PARTY.md. No third-party receipt source is bundled. The optional
portable Python download retains upstream notices and pinned checksums. LICENSE
and THIRD_PARTY.md now survive installed-plugin staging and participate in the
same Node/Python identity algorithm; legacy payloads lacking notices remain
compatible. A staging regression and the existing cross-language identity test
cover this change. Verification algorithms remain unchanged.

## Marketplace readiness

Added `.agents/plugins/marketplace.json` using the Plugin Creator's existing
schema builder. The root-relative `./` source is intentionally different from
the scaffold subdirectory convention. The name reader and plugin validator pass.
Actual Codex 0.158.0-alpha.2.1 added this local repository marketplace, installed
`claim-verifier@codex-claim-verifier` version 0.2.0, preserved configuration, and
reached WAITING FOR HOOK REVIEW in an isolated home. No schema was invented and
no production marketplace/trust settings were changed.

## GitHub-only installation

README uses `npx --yes --package <GitHub release tarball URL> claim-verifier setup`.
There is no claim that npm registry installation works. CLI help and recovery
messages likewise reference the GitHub release channel. The real local packed
asset passed setup, version, doctor, audits, dry-run, repeated setup, and exact
configuration-preservation checks without local development paths. Public HTTPS
installation and pinned remote marketplace transport are checked after release.

## Release gates and blockers

- Source cleanup, secret/local-path review, README, MIT license, exclusions,
  public metadata, automated checks, plugin/package validation, and actual local
  tarball/marketplace smoke are complete; see [verification.md](verification.md).
- Authenticated REST access and SSH access to the exact requested public GitHub
  repository are available. No release-preparation blocker remains.
- Human `/hooks` trust, trusted-session fake/verified claims and READY acceptance,
  and live Desktop delivery remain pending and are allowed Public Preview limits.
- npm publication is excluded. Optional CI is deferred; no interactive trust
  acceptance is represented as a CI or automated result.
