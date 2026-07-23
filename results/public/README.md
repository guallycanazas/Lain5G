# Public Results

This tree is the publication boundary for sanitized result summaries. It does not accept runtime logs, packet captures, protocol payloads, subscriber or SIM identifiers, credentials, local addresses, host paths, RF operating details, or hardware serials.

The repository contains three passing software-validator summaries and one blocked software-simulation attempt. These are sanitized reports, not raw independently reviewable protocol evidence. The environment record reports only non-sensitive verification-host tool versions and is explicitly not scenario evidence. Consult each result's classification and limitations before making a claim.

## Layout

- `environment/` contains sanitized host-tool summaries.
- `4g-lte-sim/`, `4g-ims-sim/`, `5g-sa-sim/`, and `5g-vonr-sim/` contain schema-conforming scenario result JSON.
- `tables/` contains sanitized aggregate CSV or JSON evidence.
- `summaries/` contains sanitized aggregate JSON or Markdown evidence.
- `public-result.schema.json` is the result contract.
- `environment-summary.schema.json` is the environment-summary contract.

Empty publication directories use `.gitkeep`. Remove it when the directory gains a public artifact.

## Export

Prepare a small JSON summary containing only the fields in `public-result.schema.json`. Do not use a log, capture, command transcript, runtime metadata dump, or protocol message as input.

Run:

```text
python3 scripts/results/export-public-result.py safe-summary.json
```

Use `-` to read the safe summary from standard input. The exporter validates the source-commit field format and release value, verifies hashes for Git-versionable public references, scans every field and value, and writes normalized JSON to `results/public/<scenario>/<run_id>.json`. It does not prove that a clean checkout of the named commit produced the input summary; that provenance must be established by the execution procedure. Reusing a run ID is idempotent only when the normalized content is identical.

The command label is a short human description, not shell text or an argument list. Configuration references point to public repository files and include SHA-256 hashes. Referenced simulation identities are synthetic test vectors, not real subscribers. Associated files are limited to sanitized artifacts under `tables/` or `summaries/` and also include SHA-256 hashes.

## Classifications

`result_classification` describes the evidence scope:

- `VALIDATED`: all claimed criteria have adequate safe evidence for the stated scope.
- `PARTIALLY_VALIDATED`: only some claimed criteria have adequate safe evidence.
- `NOT_VALIDATED`: the available evidence does not validate the scenario.
- `SIMULATION_ONLY`: evidence is limited to software simulation and makes no RF or hardware claim.
- `DRY_RUN_ONLY`: only a non-executing plan or dry-run control path was evaluated.

`execution_status` independently records whether the invocation was `PASS`, `FAIL`, `BLOCKED`, or `SKIPPED`. A successful process exit does not by itself establish validation.

For a blocked attempt, record the real UTC start and end, measured end-to-end duration, `execution_status` as `BLOCKED`, and normally `result_classification` as `NOT_VALIDATED`. Record every scenario criterion reached by the validator as `NOT_ASSESSED`; if execution never entered criterion evaluation, record a single completion criterion as `NOT_MET` and state that no scenario criterion was assessed. A command timeout can be shorter than the end-to-end duration because startup and cleanup remain inside the measured attempt. Use `DRY_RUN_ONLY` only when the evidence truly consists of a dry run. State the non-sensitive reason in `limitations`; do not attach logs.

For a completed passing software simulation, record `execution_status` as `PASS`, each criterion outcome from safe evidence, and `result_classification` as `SIMULATION_ONLY`. Use `VALIDATED` only when the declared scope and every criterion are supported without overstating simulation, RF, or hardware coverage.
