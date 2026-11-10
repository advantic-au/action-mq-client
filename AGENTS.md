# AGENTS.md

## What this repository is

This repo *is* a **GitHub composite Action** (no compiled artifact, no package). Consumers reference it as
`uses: <owner>/action-mq-client@<ref>`. There is no source to build, no test suite, and no README.

It downloads and installs the **IBM MQ client libraries** (Linux x64, Linux ARM64/PPC64LE/S390X, Windows x64,
macOS) and exports their paths to the caller's workflow.

## Layout

| Path | Role |
| --- | --- |
| `action.yml` | The composite action: inputs, outputs, download/cache/extract/install steps |
| `aliases.json` | Alias → concrete version per OS+arch (currently `latest`, `10.0`, `9.4`, `9.3`) |
| `checksums.txt` | 166 lines: sha256 for every IBM archive ever published. The allow-list and integrity root |
| `sync-client.py` | Scrapes IBM download directories and refreshes `checksums.txt` |
| `scripts/version-alias.sh` | Resolves an alias/version to a concrete version for a given OS+arch |
| `scripts/download-client.sh` | Downloads one archive, verifying it against `checksums.txt` |
| `scripts/next-version.py` | Works out the next semver version from the conventional commits since the last release |
| `requirements.txt` | Fully pinned deps for `sync-client.py` (bumped by Renovate) |

## Commands

```bash
# Resolve an alias (VERSION then OS+ARCH concatenated); requires jq
./scripts/version-alias.sh latest LinuxX64        # -> 10.0.1.0

# Download one archive into a target dir; prints the full archive path
./scripts/download-client.sh 10.0.1.0 LinuxX64 /tmp/dlc

# Refresh checksums.txt from IBM (network + large downloads; rewrites the file in place)
pip install -r requirements.txt
python sync-client.py checksums.txt

# Local lint (same tools/version of the CI checks)
shellcheck scripts/*.sh
uv tool install zizmor && zizmor --format sarif .

# Work out the next version for a range of commits (prints `none` if nothing warrants a release)
python3 scripts/next-version.py v1.0.0
```

CI is `.github/workflows/ci.yml`, which runs the action for real on Windows/Ubuntu/macOS/ubuntu-arm and then
calls `dspmqver`. "Testing a change" means running that workflow (`workflow_dispatch` is enabled) - there is
nothing to run locally that exercises `action.yml` end to end.

## How the pieces fit

1. `action.yml` `alias` step calls `version-alias.sh "${client-version}" "${os}${arch}"`, producing the concrete
   version used for both the cache key and the download.
2. `download-client.sh` picks a base URL + archive filename from the **OS argument**, appends the version, and
   hard-fails if that exact archive is absent from `checksums.txt` (no hash = not allowed to download).
3. The archive is cached in the caller's workspace under key `mqc-<os><arch>-<version>`, then extracted
   per-OS, and the resulting paths are exported via `GITHUB_PATH` / `GITHUB_ENV` and as action outputs.

## Releases

Merging to `main` releases automatically; there is no separate release step. `ci.yml` has a `release` job
that `needs: [install, cross]`, so a red CI run **skips** the release rather than failing it. That job calls
the reusable `.github/workflows/release.yml`, which:

1. exits early if `HEAD` is not `origin/main`, so a queued run never releases a stale commit,
2. computes the next version, and exits with a summary if the range warrants no release,
3. creates `vX.Y.Z` (`gh release create … --generate-notes`) and force-moves the moving tags.

There is no release-side smoke test: `action.yml` itself is verified by the `install` and `cross` jobs that
gate this one, so re-running the action here would only duplicate work on a second runner.

Ref scheme: `vX.Y.Z` tags are immutable release tags; `v1` is a moving major tag; `main` is development.
`stable` is a deprecated moving tag kept only while consumers migrate to `v1` - the workflow moves it when
it exists, so deleting the tag later needs no workflow change. Both `v1` and `stable` are advanced with
`gh api`, never `git push`, so `persist-credentials: false` stays intact.

`scripts/next-version.py` picks the bump from the **conventional commits** since the last `vX.Y.Z` tag, taking
the highest of:

| Commit | Bump |
| --- | --- |
| `!` before the `:` in the type (`feat!:`, `fix(scope)!:`) | major |
| `BREAKING CHANGE:` / `BREAKING-CHANGE:` in the body | major |
| `feat:` / `feat(scope):` | minor |
| `fix:` / `fix(scope):` | patch |
| `chore`, `docs`, `ci`, `test`, `build`, `style`, `refactor`, anything unrecognised | none |

A range where every commit is `none` produces no release at all. `release.yml` also accepts a
`workflow_dispatch` `version` input for bootstrapping (`gh workflow run release.yml -f version=1.0.0`) and
as an escape hatch when a range deliberately classifies as `none`.

## Non-obvious gotchas

- **`os`/`arch` inputs are not the runner.** They default to `runner.os`/`runner.arch` but can be set to any
  supported target to *cross-download* a client for a different platform (see the `cross` job in `ci.yml`).
  Values are case-sensitive: `Linux`/`Windows`/`macOS` and `X64`/`ARM64`/`S390X`/`PPC64LE`.
- **Cross-arch clients are downloaded but not installed.** `install-linux` and `install-macos` additionally
  require `inputs.arch == runner.arch` before touching `GITHUB_PATH`. The Windows install condition checks
  `runner.os == 'Windows'` twice instead of comparing `inputs.os` - a known quirk, leave it alone unless fixing it.
- **`runner.arch` never produces `PPC64LE`/`S390X`**, so those keys in `aliases.json` are only reachable via
  explicit input.
- The macOS archive is a single arch-independent `.pkg`, so `macOSARM64` and `macOSX64` entries in
  `aliases.json` must be edited together by hand.
- **`sync-client.py` rewrites `checksums.txt` in place** (arg `sys.argv[1]`), reorders every line to match IBM's
  directory-listing order (the URLs carry `?C=M;O=A`), reuses existing hashes to avoid re-downloading, only
  downloads archives that have no recorded hash, and **drops entries for archives IBM no longer publishes**.
  Expect noisy diffs that move unrelated lines; that is normal.
- `download-client.sh` uses `grep` **as a regex** (not `grep -F`) against `checksums.txt`, and the hash tool
  differs by host (`shasum -a 256` on macOS, `sha256sum` elsewhere).
- Workflow security posture is enforced: top-level `permissions: {}`, `persist-credentials: false` on
  checkouts, and `.github/zizmor.yml` allows floating refs only for `actions/*` and `github/*` - every other
  `uses:` must be SHA-pinned with a trailing `# vX.Y` comment. `static_analysis.yml` runs zizmor weekly/in PRs.
- `.github/workflows/sync_client.yml` runs daily (`40 4 * * *`) on the **`client_sync` branch**, commits as
  `feat: sync MQ client list`, pushes, and opens a PR against `main` with the same title. Those commits are
  automated, not hand-authored. The subject is deliberately `feat:` - an unrecognised type such as the old
  `client:` would never release, while `feat:` makes each merged sync a **minor**, since a newly published MQ
  version is new supported functionality.
- **A `chore:`/`docs:`/`ci:` prefixed *breaking* change releases as nothing.** Only a `!` before the colon or a
  `BREAKING CHANGE:`/`BREAKING-CHANGE:` footer makes `next-version.py` cut a major, and only `feat:`/`fix:`-class
  commits make a range release at all. Anything else is silently skipped, with the reason in the run's job summary.
- **If PRs are squash-merged, the PR title becomes the commit subject on `main`** and therefore drives the bump -
  a PR titled `Fix cache key` releases nothing. Merge commits are more forgiving, because `git log` then sees the
  branch's own conventional commits.
- `renovate.json` groups non-major `github-actions` updates into a single automerged PR (`groupName` on the rule that
  already matched `minor`/`patch`/`pin`/`digest`), so one merge means one patch release rather than one per bump.
  Do **not** add `major` to that `matchUpdateTypes` list - `separateMajorMinor` defaults to true and majors need review.
- `release.yml` is reached with `workflow_call` from `ci.yml`, **not** `workflow_run`: zizmor's `dangerous-triggers`
  audit flags `workflow_run` at High severity with no exemption, and `workflow_call` avoids needing a suppression.
  Its `concurrency` group is a literal string rather than `${{ github.workflow }}`, which inside a reusable
  workflow would resolve to the caller's name.
- Tag pushes made with `GITHUB_TOKEN` do not trigger workflows, so a new release tag does not re-run `ci.yml` or
  `static_analysis.yml` (both keyed on `main`) and zizmor never scans a tag ref. That is intended, not a gap.

## Conventions

- Shell scripts: `set -e`, resolve their own directory via `realpath "$0"`, read args positionally (`$1`, `$2`,
  ...), and print the artifact path to stdout so `action.yml` can capture it into `GITHUB_OUTPUT`.
- Errors go to stderr with a non-zero exit (`>&2 echo ...; exit 1`).
- Python: plain script, `snake_case`, module-level procedural code, no functions beyond the helpers in
  `sync-client.py`. `scripts/next-version.py` follows the same style and uses only the standard library, so
  `requirements.txt` stays scoped to `sync-client.py`.
- Dependency bumps are Renovate PRs (`renovate.json`, `config:best-practices`, `minimumReleaseAge: "7 days"`, no
  schedule set); don't hand-edit versions in `requirements.txt` or workflow `uses:` lines. Non-major
  `github-actions` updates are automerged (grouped, see the gotchas above); pip bumps are neither grouped nor
  automerged. Commit subjects come from Renovate, so a merged dependency PR is a `fix`-class commit and releases
  a patch.
- Removing support for an old MQ version means deleting its lines from `checksums.txt` and its alias entries
  from `aliases.json` (see commit `Remove version 9.2`).
- `aliases.json` is maintained **by hand**, one entry per `major.minor` series (`latest`, `10.0`, `9.4`, `9.3`) plus
  one key per supported OS+arch. When a new series appears, bump `latest`, add the series key, and bump the new
  `latest` patches of the previous series - don't touch older frozen series.
- A new upstream archive in `checksums.txt` does **not** get an alias automatically, and `sync-client.py` *prunes*
  entries IBM no longer publishes, so an alias can silently point at a version that is no longer downloadable
  (`download-client.sh` then fails with `Unknown archive`). Keep the pinned versions honest against
  `checksums.txt`: `9.4` lost its `macOSARM64`/`macOSX64` keys when IBM stopped publishing those `.pkg` files, and
  `9.3` covers only LinuxX64/WindowsX64 (`9.3.5.0`) plus LinuxPPC64LE/S390X (`9.3.0.0`) because IBM never published
  9.3 clients for ARM64 or macOS. An unresolvable alias exits non-zero instead of failing over to another version.
