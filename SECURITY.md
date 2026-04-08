# Security Policy

## Supported Versions

The following versions of this project are currently supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| latest  | :white_check_mark: |

---

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please follow responsible disclosure and **do not** open a public GitHub issue.

### How to Report

1. **Email**: Send a detailed report to the project maintainers (add your security contact email here).
2. **Include** the following in your report:
   - A clear description of the vulnerability
   - Steps to reproduce the issue
   - Potential impact / severity assessment
   - Any suggested fixes or mitigations (optional but appreciated)

### Response Timeline

- **Acknowledgement**: Within 48 hours of receiving your report.
- **Initial assessment**: Within 5 business days.
- **Resolution or mitigation**: Dependent on severity — critical issues will be prioritized.

---

## Security Best Practices for Contributors

### Secrets & Credentials

- **Never** hardcode API keys, passwords, or secrets in source code or commit them to the repository.
- All sensitive values (e.g. `DATABASE_URL`, `GEMINI_API_KEY`, `EXA_API_KEY`) must be stored as **GitHub Actions Secrets** and referenced via `${{ secrets.SECRET_NAME }}` in workflows.
- Use `.env` files locally and ensure `.env` is listed in `.gitignore`.

### Environment Variables

The following environment variables are required and must be configured as GitHub Secrets in CI:

| Variable         | Description                        |
| ---------------- | ---------------------------------- |
| `DATABASE_URL`   | PostgreSQL connection string       |
| `GEMINI_API_KEY` | API key for Google Gemini          |
| `EXA_API_KEY`    | API key for Exa search             |

### Dependencies

- Keep all dependencies up to date and regularly audit for known vulnerabilities.
- Use `pip audit` or tools like [Dependabot](https://github.com/dependabot) to detect vulnerable packages.
- Pin dependency versions in `requirements.txt` to avoid supply-chain risks.

### Database Security

- Never expose the database directly to the public internet.
- Use strong, randomly generated passwords for all database users.
- Apply the principle of least privilege — CI/CD database users should only have the permissions they need.

### Pull Requests from Forks

GitHub Actions **does not** pass secrets to workflows triggered by pull requests from forked repositories. This is intentional and expected behavior to prevent secret exfiltration.

---

## Scope

This policy applies to the source code, CI/CD pipeline, and infrastructure configuration of this repository.

Issues in third-party libraries or services (e.g. PostgreSQL, Prisma, FastAPI) should be reported to their respective maintainers.

---

## Attribution

We appreciate responsible disclosure and will acknowledge security researchers who report valid vulnerabilities (with their permission).
