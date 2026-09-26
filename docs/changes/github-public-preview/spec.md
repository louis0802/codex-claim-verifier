# Specification — GitHub Public Preview

## Public behavior

Users can obtain the 0.2.0 package from GitHub, run setup without npm registry
publication, retain existing configuration, and inspect installation using the
implemented `setup`, `doctor`, `audit latest`, `audit list`, and `version` commands.
Quick Start must use a genuinely tested GitHub distribution path. On supported
macOS hosts setup reaches the human hook-review boundary; installation does not
imply trust or a READY diagnostic.

The README explains observed execution evidence, the optional GPT-6 Luna semantic
extractor, deterministic decisions, all six verification levels, and the three
separate enforcement modes. It discloses missing Bash exit status, checked-run
coverage, bounded Stop continuation, variable visible receipts, and pending
trusted Desktop verification. A repair instruction follows the main agent's
ordinary permission flow; verification never triggers a push or deployment.

## Acceptance criteria

- A1: Source, package, and release contain no private data, runtime ledgers,
  workstation-specific links, build residue, or embedded source/package archives.
- A2: LICENSE and package/plugin/README license metadata agree; upstream notices
  are retained and provenance is disclosed.
- A3: Public title, owner, repository URLs, description, version 0.2.0, and a valid
  repository marketplace catalog are consistent with the requested destination.
- A4: README covers the public commands, levels, enforcement, security model,
  configuration, audit privacy, and every required pending platform limitation.
  CLI help/error guidance must use the GitHub release channel.
- A5: Python and Node suites, syntax checks, plugin and package validation pass;
  a real isolated tarball setup preserves configuration, reports 0.2.0, and
  exposes working doctor/audit commands without development paths.
- A6: The complete reviewed public source is committed to `main`, pushed only to
  the exact SSH remote, and tagged `v0.2.0` without overwriting an existing tag.
- A7: GitHub has a Public Preview pre-release with matching tarball, checksum,
  actual test count, known limitations, and four requested tracking issues.
- A8: A real public GitHub installation is exercised after release. Manual trust,
  fake/verified live claims, and trusted READY remain explicitly pending until
  performed by the user in a reviewed session. npm remains unpublished.

## Open decisions

- License resolved: the user selected MIT, copyright 2026 Louis.
- Authenticated GitHub REST access to the requested repository is verified.
  The token remains in the process environment and is never printed or packaged.
