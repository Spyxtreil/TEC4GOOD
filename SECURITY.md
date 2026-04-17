# Security Policy

## Supported Versions

This is a small educational project. Only the latest commit on `main` is supported.

| Version | Supported |
|---------|-----------|
| `main` (latest) | ✅ |
| any other tag/branch | ❌ |

## Reporting a Vulnerability

If you believe you have found a security vulnerability, **do not open a public issue**.

Please report it privately by email to **adrngeng@gmail.com** with:

- A clear description of the vulnerability.
- Steps to reproduce (PoC if possible).
- Affected file(s) and commit hash.
- Your assessment of the severity (low / medium / high / critical).
- Whether you want to be credited in the fix.

### Response timeline (best effort — student project)

| Stage                | Target       |
|----------------------|--------------|
| Acknowledgement      | 72 hours     |
| Initial assessment   | 7 days       |
| Fix or mitigation    | 30 days      |
| Public disclosure    | After fix    |

## Scope

### In scope

- Python scripts (`adhd_activity_planner.py`, `nutrition_advisor (1).py`, `main.py`).
- Arduino sketches (`pulso_simple.ino`, `sensooooor2.ino`).
- CI workflows in `.github/workflows/`.
- Dependency pinning (`requirements*.txt`, `pyproject.toml`).

### Out of scope

- Issues in third-party libraries (report upstream to SparkFun, etc.).
- Attacks that require physical access to an already-flashed Arduino.
- Clinical accuracy of the output — this is covered by the medical
  disclaimer in `TERMS_AND_CONDITIONS.md`, not by the security policy.
- Social engineering.

## Safe-harbour

We will not pursue legal action against researchers who:

- Make a good-faith effort to avoid privacy violations, data loss, and
  service disruption.
- Report vulnerabilities privately and give us reasonable time to fix
  before public disclosure.
- Do not exploit a vulnerability beyond what is necessary to demonstrate it.
