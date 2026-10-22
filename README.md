# MQ client download

[![Continuous Integration](https://github.com/advantic-au/action-mq-client/actions/workflows/ci.yml/badge.svg)](https://github.com/advantic-au/action-mq-client/actions/workflows/ci.yml)

Download and install the IBM MQ client libraries on a runner, so later steps can build
or test against MQ (`dspmqver`, the MQ client libraries, ...).

The action:

1. resolves the requested version alias (e.g. `latest`) to a concrete version for the target OS and
   architecture,
2. downloads that archive from IBM's public download server, verifying it against a sha256 allow-list,
3. caches the archive across runs,
4. extracts and installs it, and puts the resulting binaries and libraries on `PATH` /
   `LD_LIBRARY_PATH` for the rest of the job.

## Usage

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - name: Install MQ client
        uses: advantic-au/action-mq-client@stable
        with:
          client-version: latest

      - run: dspmqver
```

Pin a tag (`@stable`) or any other ref, such as `@main` for the development state.

### Version pinning

```yaml
      - uses: advantic-au/action-mq-client@stable
        with:
          client-version: 10.0.1.0   # exact version
```

`client-version` accepts an exact version (`10.0.1.0`) or one of the aliases in
[`aliases.json`](aliases.json):

| Alias | macOS ARM64 | macOS x64 | Linux x64 | Linux ARM64 | Linux PPC64LE | Linux S390X | Windows x64 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `latest` | 10.0.1.0 | 10.0.1.0 | 10.0.1.0 | 10.0.1.0 | 10.0.1.0 | 10.0.1.0 | 10.0.1.0 |
| `10.0` | 10.0.1.0 | 10.0.1.0 | 10.0.1.0 | 10.0.1.0 | 10.0.1.0 | 10.0.1.0 | 10.0.1.0 |
| `9.4` | - | - | 9.4.5.1 | 9.4.5.1 | 9.4.5.1 | 9.4.5.1 | 9.4.5.1 |

Anything not in the table is passed through unchanged, so an exact version such as `9.4.4.0`
works as long as it is listed in [`checksums.txt`](checksums.txt).

### Cross-platform downloads

`os` and `arch` describe the MQ **client** to fetch, not the runner. They default to
`runner.os` / `runner.arch`, but can be set to another target to fetch an archive for a
platform you are not running on:

```yaml
      - uses: advantic-au/action-mq-client@stable
        id: mq
        with:
          client-version: latest
          os: Linux
          arch: S390X
```

Valid values are `Linux`, `Windows`, `macOS` for `os` and `X64`, `ARM64`, `PPC64LE`, `S390X`
for `arch` (case sensitive).

When the requested target differs from the runner, the archive is still downloaded and verified,
and its path is exposed through the `client-archive-path` output, but extraction and the
`PATH` / `LD_LIBRARY_PATH` changes only happen when the requested target matches the runner
itself.

## Inputs

| Input | Required | Default | Description |
| --- | --- | --- | --- |
| `download-path` | yes | `${{ runner.temp }}/mqc_download` | Directory the archive is downloaded to, and the directory that is cached |
| `client-version` | yes | `latest` | MQ client version, or an alias such as `latest` |
| `os` | yes | `${{ runner.os }}` | OS of the MQ client: `Linux`, `Windows`, `macOS` |
| `arch` | yes | `${{ runner.arch }}` | Architecture of the MQ client: `X64`, `ARM64`, `PPC64LE`, `S390X` |

## Outputs

| Output | Description |
| --- | --- |
| `client-version` | The concrete version that was resolved, e.g. `10.0.1.0` for `latest` |
| `client-archive-path` | Full path of the downloaded archive |
| `client-install-path` | Where the client is installed for the requested `os`: `$HOME/mqc` on Linux and Windows, `/opt/mqm` on macOS |

```yaml
      - uses: advantic-au/action-mq-client@stable
        id: mq
        with:
          client-version: latest

      - run: |
          echo "MQ ${{ steps.mq.outputs.client-version }} installed at ${{ steps.mq.outputs.client-install-path }}"
          dspmqver
```

## Supported platforms

| Target | Archive | Installed to | Environment set |
| --- | --- | --- | --- |
| Linux x64 | `IBM-MQC-Redist-LinuxX64.tar.gz` | `$HOME/mqc` | `PATH` += `$HOME/mqc/bin`, `LD_LIBRARY_PATH` = `$HOME/mqc/lib64` |
| Linux ARM64, PPC64LE, S390X | `IBM-MQ-Advanced-for-Developers-Non-Install-<arch>.tar.gz` | `$HOME/mqc` | same as Linux x64 |
| Windows x64 | `IBM-MQC-Redist-Win64.zip` | the user's home directory (`\mqc`) | `PATH` += `%HOMEDRIVE%%HOMEPATH%\mqc\bin64` |
| macOS (ARM64, x64) | `IBM-MQ-DevToolkit-MacOS.pkg` | system-wide install (`installer -target /`), binaries in `/opt/mqm` | `PATH` += `/opt/mqm/bin` |

These are the platform combinations the action supports: macOS is served by a single
architecture-independent `.pkg`, and the Linux architectures above are the ones IBM publishes a
client for.

## Caching

Downloads are cached with `actions/cache`, keyed on `mqc-<os><arch>-<resolved version>`, using
`download-path` as the cached directory. The first run for a given platform and version
downloads the archive; later runs restore it from the cache.

## Integrity

Every download is verified against [`checksums.txt`](checksums.txt), a sha256 allow-list of
the IBM archives this action is willing to install. An archive that is not in the list is
rejected before it is used, so `client-version` values that IBM has withdrawn fail the job
rather than silently installing something else. `checksums.txt` is refreshed from IBM's
download listings by a scheduled workflow.

## Requirements

The action is a composite action that runs shell scripts, so it needs the tools present on the
GitHub-hosted runner images: `bash`, `jq` and `curl` (plus `tar`, and `7z` on Windows). The
`ci.yml` workflow exercises it on `windows-latest`, `ubuntu-latest`, `macos-latest` and
`ubuntu-24.04-arm`.

macOS installation uses `sudo installer`, so it needs a runner where `sudo` is available.

## License

Apache-2.0 - see [LICENSE-APACHE](LICENSE-APACHE).
