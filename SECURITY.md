# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| `main`  | ✅        |

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Email **abdulmunim.personal@gmail.com** with the subject line `[SECURITY] NeuroAgent — <brief title>` and include:

- A clear description of the vulnerability
- Steps to reproduce (proof-of-concept code if applicable)
- Potential impact and attack surface
- Any suggested mitigations

You will receive an acknowledgement within **48 hours**. Please allow up to **90 days** for a fix to be developed and deployed before disclosing publicly. We will coordinate a disclosure date with you and credit you in the release notes unless you prefer to remain anonymous.

## Scope

The following are in-scope for security reports:

- **Authentication and authorisation** — JWT issuance and validation (`backend/app/services/auth_service.py`, `backend/app/utils/security.py`)
- **Agent tool execution** — sandboxed code execution, browser automation, and arbitrary HTTP calls (`backend/app/agent/tools/`)
- **API input validation and rate limiting** — all `/api/v1/` endpoints
- **Secret handling** — improper logging or exposure of API keys, tokens, or PII

## Out of Scope

- Vulnerabilities in third-party dependencies — report these upstream (PyPI, npm, or the relevant vendor)
- Issues that require physical access to infrastructure
- Social engineering or phishing attacks targeting maintainers
- Theoretical weaknesses without a demonstrated exploit path

## Preferred Languages

Reports may be submitted in English.
