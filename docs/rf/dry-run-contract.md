# SDR dry-run contract

## Scope

This contract applies when `LAIN5G_DRY_RUN=true` is passed to the scripts in:

- `deployments/4g-volte/x310/scripts/`
- `deployments/5g-sa-x310/scripts/`
- `deployments/5g-nsa-x310/scripts/`

It also applies to RF plans returned by the deployment API when `execute` is
false. Dry-run is a planning mode, not an RF readiness check and not evidence
that a scenario is authorized or operational.

## Required behavior

In dry-run mode, an SDR script must:

- Exit successfully without executing an RF, RAN, UHD, device, Docker, network,
  route, container, volume, or service command.
- Leave containers, networks, volumes, host settings, run artifacts, temporary
  logs, runtime directories, RF marker files, and configuration unchanged.
- Avoid sourcing or printing effective `.env`, channel-plan, safety-manifest,
  device, or runtime values.
- Print only a fixed, high-level plan for the requested operation.
- Omit operator notes, addresses, identifiers, channel and frequency values,
  bands, gains, durations, credentials, tokens, and hardware metadata.

RF start scripts enforce the dry-run exit before authorization inspection,
preflight, duration resolution, run-directory creation, hardware delay or
probe, marker creation, and Docker invocation. Preflight, validation, hardware,
UHD, FPGA, stop, and emergency-stop entrypoints follow the same non-mutating
rule.

Only the exact value `true` enables this shell contract. An unset value or any
other value follows normal command behavior and must not be treated as a safe
preview.

## Normal RF mode

Dry-run does not weaken normal RF controls. Normal RF starts still require:

- The scenario-specific process guard:
  `LAIN5G_ALLOW_RF_START`, `LAIN5G_ALLOW_5G_RF_START`, or
  `LAIN5G_ALLOW_5G_NSA_RF_START`.
- An RF-ready preflight and a locally supplied blocked-by-default safety
  manifest.
- Explicit authorization, an operator note, finite duration, automatic stop,
  log capture, and the scenario's isolation or attenuation checks.
- A ready core and no conflicting active RF session.
- Required local channel and device configuration.

The NSA path additionally requires authorization for all configured laboratory
frequencies, confirmation of the second RF path, and RF-session exclusivity.
The API's execution path additionally requires all acknowledgements, the exact
confirmation phrase, local RF web-control enablement, component checks, and
conflict checks.

## API plans

For `execute=false`, the API returns a synthetic command containing only
`LAIN5G_DRY_RUN=true` and the selected script path. It does not execute the
script and does not include the requested duration or operator note. For
`execute=true`, the API retains the normal guarded command and shell preflight.

## Automated verification

`backend/tests/test_rf_dry_run_contract.py` copies only versioned shell scripts
into a temporary sandbox. It places synthetic canaries in local-config and
marker locations, traps Docker, UHD, RF, network, filesystem, and service
commands, then invokes every X310 script with `LAIN5G_DRY_RUN=true`.

The test requires zero trapped commands, an unchanged sandbox snapshot,
unchanged markers, successful fixed-plan output, and no canary or sensitive
assignment in output. Static ordering checks require the dry-run exit to occur
before each normal RF guard, RF-ready preflight, and Docker start. Separate API
tests verify plan sanitization and rejection of execution requests missing RF
acknowledgements.
