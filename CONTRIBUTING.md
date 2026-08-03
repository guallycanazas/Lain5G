# Contributing

OpenLain5G accepts reproducible fixes, documentation improvements, tests, and
well-scoped feature proposals through GitHub pull requests.

## Before Opening a Pull Request

1. Search existing issues and pull requests.
2. Keep changes focused and explain the operational or research need.
3. Do not commit generated environments, runtime state, credentials, subscriber
   data, RF plans, authorization records, captures, databases, or private logs.
4. Preserve existing profile IDs, CLI commands, environment variables, and image
   names unless the change explicitly includes a reviewed migration.
5. Keep automated tests hardware-free and RF-free.

## Validation

Run the complete safe gate from the repository root:

```bash
make softwarex-check
```

For documentation-only changes, also run:

```bash
make links-check release-artifacts-check
```

Describe any test that could not be run and why. Never enable RF merely to
complete a pull-request check.

## Pull Requests

Include a concise summary, affected profiles, verification performed, evidence
limitations, and security implications. New public result artifacts must satisfy
the schemas and sanitization rules under `results/public/`.

Security vulnerabilities must be reported privately according to
[`SECURITY.md`](SECURITY.md), not through an issue or pull request.
