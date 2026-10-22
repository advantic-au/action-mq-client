# Security policy

## Supported versions

This action is consumed by git ref, so the reference you pin decides what you run:

- The `stable` ref and `main` get fixes.
- Older refs - fixed tags and commit SHAs - are not patched. Move to a newer ref to pick up a fix.

## Reporting a vulnerability

Please report vulnerabilities privately rather than in a public issue: open the **Security** tab of
this repository and choose **Report a vulnerability**, which creates a private advisory that only
you and the maintainers can see.

Useful details to include:

- the ref you pinned (`advantic-au/action-mq-client@...`),
- the workflow step and inputs involved,
- what an attacker would gain, and the steps to reproduce it.

We will investigate, ask for anything we are missing and keep you updated on the outcome. Tell us
if you would like to be credited in the advisory or release notes.

## Scope

In scope:

- `action.yml`, `scripts/download-client.sh`, `scripts/version-alias.sh` and `sync-client.py`,
- the integrity of what gets installed: verification against `checksums.txt`, cache handling, and
  how paths and versions are resolved,
- the workflows in `.github/workflows`, for example command injection or an unpinned third-party
  action.

Out of scope:

- vulnerabilities in IBM MQ itself or in the archives this action downloads - report those to IBM,
- vulnerabilities in the GitHub-hosted runner images, or in GitHub Actions itself,
- known issues in an old MQ client version that is still published and installable.

## For consumers

- Pin a ref you trust, and review the diff when you move to a new one.
- Only archives whose sha256 is listed in `checksums.txt` are downloaded, and the hash is verified
  before the archive is used. A version that IBM has withdrawn fails the job instead of silently
  installing something else.
- The action writes into `download-path` (default `${{ runner.temp }}/mqc_download`), installs under
  `$HOME/mqc` on Linux and Windows or `/opt/mqm` on macOS, and updates `PATH` (and
  `LD_LIBRARY_PATH` on Linux) for later steps.
