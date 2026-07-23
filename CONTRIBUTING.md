# Contributing

Lain5G-Lab welcomes focused bug reports, documentation corrections, tests, and
small changes that improve reproducibility or laboratory safety.

## Before changing code

1. Search the [issue tracker](https://github.com/guallycanazas/Lain5g-lab/issues)
   for related work.
2. Open an issue before a large behavioral, dependency, scenario, or metadata
   change so its scope and evidence can be agreed.
3. Keep changes minimal and separate unrelated work.

TODO: Confirm maintainers and reviewer ownership before a final release.

## Safety and data handling

- Never commit subscriber secrets, real IMSI/MSISDN values, private keys,
  private infrastructure addresses, operational RF plans, or authorization
  records.
- Use synthetic laboratory data and redact logs before attaching them to an
  issue or pull request.
- Do not transmit RF without the required legal, technical, and institutional
  authorization. A dry run or passing software test is not RF authorization.
- Do not present container health, simulation, or historical/private evidence
  as an end-to-end result for the current revision.

## Submitting a change

1. Follow the existing style and update tests or documentation when behavior
   changes.
2. Run the smallest relevant non-RF checks. For metadata changes, validate CFF
   and JSON syntax and confirm both metadata versions match `VERSION`.
3. State the commands run, revision tested, result, and any skipped validation.
4. Describe limitations and distinguish software-only, dry-run, SDR, and
   commercial-UE evidence.
5. Submit a pull request against
   [the repository](https://github.com/guallycanazas/Lain5g-lab).

Participation is subject to [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Report
security issues according to [SECURITY.md](SECURITY.md), not in a public bug
report.
