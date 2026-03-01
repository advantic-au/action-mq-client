# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability in **action-mq-client**, please report it responsibly by emailing **security@advantic.au** instead of using the public issue tracker.

Please include the following information in your report:
- A description of the vulnerability
- Steps to reproduce the issue
- Potential impact
- Any suggested fixes (optional)

We take all security reports seriously.

## Security Best Practices

When using **action-mq-client** in your GitHub Actions workflows, follow these security best practices:

### 1. Restrict Permissions
Minimize the permissions granted to your GitHub Actions workflows:
```yaml
permissions:
  contents: read
```

### 2. Use Pinned Versions
Pin this action to a specific commit hash rather than `@stable`:
```yaml
- uses: advantic-au/action-mq-client@7bc53a7ff51e9120b59f1ca87f727a317eb00b34
```

### 3. Keep Dependencies Updated
Regularly update your GitHub Actions and dependencies to receive security patches.

### 4. Store Credentials Securely
If your workflow uses MQ credentials or connection strings:
- Store them in GitHub Secrets
- Never commit them to the repository
- Use separate secrets for different environments

### 5. Monitor for Vulnerabilities
- Enable GitHub's Dependabot alerts on your repository
- Review security advisories regularly
- Update this action when security patches are released

## Security Scanning

This action:
- Is scanned for vulnerabilities using the zizmor tool
- Follows GitHub Actions best practices

## Disclaimer

While we strive to maintain the security of this action, no software is completely risk-free. Users are responsible for:
- Keeping their GitHub Actions and dependencies up to date
- Following the security best practices outlined above
- Assessing the security implications for their use case

For more information on GitHub Actions security, see the [GitHub Actions Security Guide](https://docs.github.com/en/actions/security-guides).
