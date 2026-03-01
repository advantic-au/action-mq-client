# action-mq-client

**action-mq-client** is a GitHub Action for automating IBM MQ client setup and integration in your CI/CD workflows. This action helps you download, verify, and configure IBM MQ client libraries for use in subsequent workflow steps.

## Usage

Add the following step to your GitHub Actions workflow:

```yaml
- name: Setup IBM MQ Client
  uses: advantic-au/action-mq-client@stable
  with:
    client-version: latest
```

### Inputs

| Name | Description | Required | Default |
|------|-------------|----------|---------|
| client-version | MQ client version | yes | latest |
| download-path | Target download path for MQ client | yes | `${{ runner.temp }}/mqc_download` |
| os | OS of MQ client | yes | `${{ runner.os }}` |
| arch | Architecture of MQ client | yes | `${{ runner.arch }}` |

### Outputs

| Name | Description |
|------|-------------|
| client-version | MQ client version downloaded |
| client-archive-path | MQ client archive path |
| client-install-path | MQ client installation path |

## Example Workflow

```yaml
name: CI
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup IBM MQ Client
        uses: advantic-au/action-mq-client
        with:
          client-version: 9.3.0.2
      - name: Use MQ Client
        run: |
          echo "MQ client downloaded to ${{ steps.setup-mq.outputs.client-install-path }}"
```

## License

This action is licensed under the Apache License 2.0. See [LICENSE-APACHE](LICENSE-APACHE) for details.
