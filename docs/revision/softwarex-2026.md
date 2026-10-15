# SoftwareX revision evidence and remaining work

Audit date: 2026-10-14. Evaluated source: v1.1.3, commit
`8da4d92e4aacec8660ddd3a5be5c4c0167671de5`. This document is a revision
addendum, not a new experiment or an amendment to an existing release.

## Five-run results and timing

The [audited summary](../../results/public/summaries/v1.1.3-cloud-five-run-20260818.md)
now includes each observation and the inclusion rule. The
[machine-readable audit](../../results/public/summaries/v1.1.3-five-run-audit-20261014.json)
contains check IDs, timestamps, original-input hashes and workflow history.
The derivation is executable with `scripts/revision/build_v113_audit.py` using
the documented downloaded inputs. It does not run a network.

GitHub workflow run [32087329776](https://github.com/guallycanazas/Lain5G/actions/runs/32087329776)
uses workflow commit `8f535205a12c5a270b3382710647bef8c290af86`, but checks out
the separate v1.1.3 source commit. Do not confuse the workflow head with the
evaluated source. Its five artifact ZIP digests were verified against the API.
Each artifact expires on 2026-11-16; recovery into a local package alone does
not satisfy permanent archival.

The [source DOI](https://doi.org/10.5281/zenodo.21827907) was published on
2026-08-06 and contains one source ZIP, not the 2026-08-18 five-run artifacts.
The ZIP MD5 matches Zenodo's receipt; all 624 contained files match the checked
out v1.1.3 source. Its `63e0615` folder prefix is the annotated tag object,
which peels to the expected `8da4d92` source commit. It is not a source mismatch.
Its older v1.1.0 operational baseline must remain labelled as such.

The paper's Table 4 values (40 s LTE and 12 s 5G) do not describe the five-job
series. Their provenance is unresolved: the earlier successful single-job
workflow step durations were 49/15, 42/15 and 41/12 s. Replace Table 4 with
the five audited rows; do not infer that 40 s belongs to a particular run.

Timing includes scenario setup, start, validation and the EXIT-trap stop.
Prior host preparation and image pulls are excluded. Container caching,
registry bandwidth, runner scheduling, CPU contention, polling intervals,
database initialization and protocol startup can affect durations. No manual
baseline was measured; no numeric time saving is justified.

## Concrete reuse example

Run after installing backend development dependencies:

```bash
.venv/bin/python scripts/revision/demo_profile_reuse.py
```

The example uses a temporary project, changes the 5G TAC to 9 and DNN to
`labnet`, validates the profile, previews and applies the five effective-file
changes, verifies idempotence, and restores the prior effective contents.
It keeps the edited declarative profile for intentional reuse. It neither
starts Docker nor emits RF. It was also executed against a separate extracted
v1.1.3 source tree using the same example and the revision host's dependency
environment. That demonstrates the evaluated release's configuration API,
not a historical experiment or runtime interoperability with altered parameters.

Files affected: `deployments/5g-sa/.env`, `open5gs/amf.yaml`,
`open5gs/smf.yaml`, `ueransim/gnb.yaml` and `ueransim/ue.yaml` (the latter
four under `deployments/5g-sa`). Backup/restore applies to effective files;
it is not a version-control rollback of the central profile. The example
initializes a private environment before applying, so restoration checks have
an existing-file baseline.

Adding a completely new scenario requires code integration in the profile and
deployment registries, lifecycle actions, validation scripts, and tests. A YAML
file alone is insufficient. Replacing a core also needs compatible provisioning,
protocol configuration and validator adapters. No such replacement was executed.

## Technical comparison with open5Gcube

The original paper [arXiv:2505.14501](https://arxiv.org/abs/2505.14501)
and the [public implementation](https://github.com/open5Gcube/open5Gcube/tree/cd2e1fc208f8a71f8adff196752aa08d713d3d68)
were consulted. Access date: 2026-10-14. The implementation snapshot is from
2026-10-09; it must not be presented as the exact implementation evaluated in
the 2025 paper. This is a source inspection, not a runtime comparison.

| Operation | OpenLain5G v1.1.3 | open5Gcube inspected snapshot | Interpretation |
|---|---|---|---|
| Lifecycle | Common scenario CLI and FastAPI/React controls | Make stack targets and WebUI | Both unify lifecycle management |
| Configuration | Central profiles, diff/apply and effective-file backup | Global/local environment and stack/module configuration | Different configuration contracts; both reusable |
| Components | Four public LTE/SA software/RF profiles | Multiple 2G/4G/5G stacks and component/version combinations | open5Gcube has broader stack coverage |
| Hosts | Documented local laboratory host | SSH-based distributed container management | No claim of broader multi-host coverage for OpenLain5G |
| Validation | Service, protocol, registration/session, address/tunnel, local gateway traffic | Robot keywords for readiness, registration, session and tunnel-bound Internet ping | Stage and tunnel checks are not exclusive to OpenLain5G |
| Evidence | Scenario/run records, configuration identity, bounded diagnostics and sanitized public exports | Test data collection, container logs and version metadata | Compare concrete formats and workflows, not absence of evidence |
| RF workflow | Default-deny preflight, finite duration and emergency-stop paths | Physical SDR stacks and clock/RAN-host configuration | No claim of absence of RF safeguards in the alternative |

Inspection anchors: OpenLain5G `lain5g`,
`src/backend/app/services/profile_config_service.py`,
`src/backend/app/services/deployment_registry.py`,
`deployments/4g-lte-sim/scripts/validate.sh`,
`deployments/5g-sa/scripts/validate.sh`; open5Gcube `README.md`, `Makefile`,
`tests/common.resource` and `tests/targets.mk` at the linked commit.

The defensible contribution is packaging a particular scenario, guard and
evidence contract in one operator workflow. Do not claim novel telecom
protocols, uniquely available stage validation, demonstrated superiority,
or measured productivity gains. A useful second example for the manuscript is
the same setup/start/validate/stop command pattern across software profiles,
with protocol-specific validation results in the original five-run artifacts.

## Physical and IMS evidence boundaries

Figure 4 of the supplied preprint shows handset-reported LTE/5G SA service
state and IMS registration, with displayed signal levels of -88 and -83 dBm.
These are two displayed observations, not calibrated signal distributions,
throughput measurements, packet-transfer evidence, calls, or voice-quality data.
No synchronized capture binds these screenshots to a particular source commit.

| Evidence tier | Minimum evidence | Status for the supplied physical observations |
|---|---|---|
| IMS infrastructure | Processes/endpoints available | Described infrastructure; not a call |
| IMS registration | Correlated SIP registration exchange and UE state | Handset reports registered; correlated trace not supplied |
| Call establishment | Correlated INVITE, final response, ACK and termination | Not supplied |
| Media | Bidirectional media counters/capture tied to negotiated endpoints | Not supplied |
| Voice quality | Defined instrument, codec, duration and repeated measurements | Not supplied |
| User-plane data | UE-bound transfer with destination, bytes, timing and logs | Not demonstrated by status screens |

Cx/Diameter and media validation must be reported per tested configuration.
Do not generalize separate historical/internal IMS experiments to all four
public profiles. Remove "active voice and data connectivity" from Section 3.2.

The source contains an internal NSA descriptor and scripts, but NSA is outside
the four-profile public catalog and the reported experimental series. Narrow
Section 2 to LTE and 5G SA; file presence is not operational validation.

## RF measurement and compatibility protocol - not executed

The lab operator must document authorization for the particular site, band,
bandwidth and operating mode under the applicable local rules before activation.
Have the institution confirm the required permission; software acknowledgments
do not grant spectrum rights. Prefer a verified shielded or suitably attenuated
cabled setup, with a link-budget and equipment-rating review, finite duration,
operator supervision, and tested emergency stop. Avoid assuming an example
attenuation value is safe for every RF path. No regulatory approval is asserted.

| Item to record | Current evidence | Required for the next lab trial |
|---|---|---|
| SDR | X-Series workflow; paper does not establish a complete model matrix | Exact model, daughterboard, UHD/FPGA, clock source and link |
| Host | Original software jobs use Ubuntu 24.04 x86_64 | CPU, RAM, kernel, NIC, MTU, tuning and contention |
| RF | No complete acquisition record supplied | Band, ARFCN/EARFCN, bandwidth, duplexing, gains, attenuation/isolation |
| UE/SIM | Representative handset screens | At least two model/firmware combinations if available; pseudonymous SIM references |
| B210/other SDRs | Not validated by these experiments | Treat as unverified until configured and tested |

Suggested planned acquisition: repeat registration/session trials per UE and
profile; report attempted and successful counts, registration time boundaries,
packet loss and RTT to a defined local endpoint, and throughput only with a
specified direction, duration and tool configuration. If adding voice, measure
call setup and bidirectional media separately. Record failures, resets, run IDs,
clock synchronization, source commit, image digests and configuration hashes.
Choose sample sizes and uncertainty reporting before acquisition; no samples
have been collected for this plan.

Planned fault cases: missing RF authorization (must refuse before activation),
subscriber mismatch (identify registration failure), and unavailable local data
endpoint (retain registration/session success but fail traffic). Execute one
change at a time in an isolated authorized lab and restore baseline afterwards.
Software guard/unit tests cannot substitute for these physical trials.

## Manuscript and archival completion checklist

1. Replace Table 4 and Section 3.1 timing prose with all five audited observations.
2. Add timing boundaries, preparation time exclusion, sequential LTE/5G design,
   hardware limitations and all prior workflow outcomes in Sections 2.3/3.1.
3. Replace the capability sentence in Section 2 with the four public profiles.
4. Restrict Section 3.2 and Figure 4 to observed handset states; add IMS tiers.
5. Expand Table 2 using the scoped technical comparison above; moderate Impact
   and Conclusions claims about ease, novelty and manual time savings.
6. Add the configuration reuse example and its non-runtime limitation.
7. Deposit a separate sanitized evidence package with DOI and checksum manifest;
   cite both source and evidence DOIs. Do not replace the published source ZIP.
8. Add actual access dates to URL references. Preserve original 2026-08-06 dates
   where documented; do not backdate new consultations. Resolve exact 3GPP
   release/version/date metadata against the authors' actual cited documents.
9. Obtain the editable manuscript and compile the revised submission before
   assigning final page/line references. No manuscript PDF has been altered here.
10. Complete or explicitly decline the additional physical measurements, second
    UE and controlled failure trials in the response letter.
