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
| `aliases.json` | Alias → concrete version per OS+arch (currently `latest`, `10.0`, `9.4`) |
| `checksums.txt` | 166 lines: sha256 for every IBM archive ever published. The allow-list and integrity root |
| `sync-client.py` | Scrapes IBM download directories and refreshes `checksums.txt` |
| `scripts/version-alias.sh` | Resolves an alias/version to a concrete version for a given OS+arch |
| `scripts/download-client.sh` | Downloads one archive, verifying it against `checksums.txt` |
| `requirements.txt` | Fully pinned deps for `sync-client.py` (bumped by Dependabot) |

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
  `client: Sync MQ client list`, pushes, and opens a PR against `main`. Those commits are automated, not
  hand-authored.

## Conventions

- Shell scripts: `set -e`, resolve their own directory via `realpath "$0"`, read args positionally (`$1`, `$2`,
  ...), and print the artifact path to stdout so `action.yml` can capture it into `GITHUB_OUTPUT`.
- Errors go to stderr with a non-zero exit (`>&2 echo ...; exit 1`).
- Python: plain script, `snake_case`, module-level procedural code, no functions beyond the helpers in
  `sync-client.py`.
- Dependency bumps are Dependabot PRs (`dependabot.yml`, weekly Monday, 7-day cooldown); don't hand-edit
  versions in `requirements.txt` or workflow `uses:` lines.
- Removing support for an old MQ version means deleting its lines from `checksums.txt` and its alias entries
  from `aliases.json` (see commit `Remove version 9.2`).
- `aliases.json` is maintained **by hand**, one entry per `major.minor` series (`latest`, `10.0`, `9.4`) plus one key
  per supported OS+arch. When a new series appears, bump `latest`, add the series key, and bump the new `latest`
  patches of the previous series - don't touch older frozen series.
- A new upstream archive in `checksums.txt` does **not** get an alias automatically, and `sync-client.py` *prunes*
  entries IBM no longer publishes, so an alias can silently point at a version that is no longer downloadable
  (`download-client.sh` then fails with `Unknown archive`). Stale entries are deleted rather than repointed: `9.3`
  was dropped entirely and `9.4` lost its `macOSARM64`/`macOSX64` keys when IBM stopped publishing those `.pkg`
  files. An unresolvable alias exits non-zero instead of failing over to another version.
