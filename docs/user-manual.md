# OpenLain5G User Manual

> The designed PDF edition is [OpenLain5G User Manual v1.1.9 candidate](manual/v1.1.9/OpenLain5G-User-Manual-v1.1.9.pdf). The versioned TeX source and image assets are in the same folder.

This manual walks through a first installation, a software-only experiment,
subscriber setup, evidence review, and shutdown. The web interface is the normal
way to operate the lab; the CLI is used to install, start, and diagnose it.

OpenLain5G is a local lab for one trusted GNU/Linux workstation. Keep the web
application bound to localhost. Do not expose its Docker control interface,
Grafana, Prometheus, or subscriber data to an untrusted network.

## 1. Install the software

Clone the repository, enter its directory, and run the installer:

```bash
git clone https://github.com/guallycanazas/Lain5G.git
cd Lain5G
./install.sh
```

The installer prepares the host tools, Docker access, private configuration,
public profile images, the SIM reader packages, and the locally built IMS helper
images. It may request your password for system package installation. Read the
commands it displays before approving them. Image preparation needs internet
access and can take several minutes.

At completion, review the installation summary. It identifies the host and
package manager, dependencies, image counts, Docker access, and elapsed time.
The full transcript is saved under
`${XDG_STATE_HOME:-~/.local/state}/lain5g/install-<UTC timestamp>.log` with
user-only permissions. A successful install means prerequisites and images
were prepared; it does not mean a network profile has been started or tested.

To preview installation actions without applying them:

```bash
./install.sh --dry-run
```

## 2. Start the web application

For full lab operation on your trusted workstation, start operations mode:

```bash
./lain5g app start --operations --open
```

Open <http://127.0.0.1:8080> if the browser does not open automatically.
Operations mode gives the local application Docker control so it can prepare
images and manage scenarios. Treat this mode as administrator access to the
host. Use the read-only mode when you only need to inspect the interface:

```bash
./lain5g app start --open
```

Read-only mode cannot start or modify lab scenarios. The application and API
health can be checked from the CLI:

```bash
./lain5g status
./lain5g app status
```

## 3. Prepare components

Open **Preparation** to review image readiness and prepare components that are
missing. The installer normally prepares the standard profiles already. The
first image build requires internet access. Preparation does not start a RAN or
transmit RF.

The CLI can inspect the host or prepare a particular profile:

```bash
./lain5g doctor
./lain5g doctor 5g-sa
./lain5g images list
./lain5g images pull 5g-sa
```

Use the **software simulation** profiles first. They run the RAN, core, and
simulated UE in containers and need no USRP or over-the-air transmission. The
Scenarios page also offers guarded X310 profiles; use those only after following
the RF section below.

## 4. Run a software scenario

1. Open **Scenarios** and select a software profile, such as **4G LTE
   Simulation** or **5G SA Simulation**.
2. Review the profile description and configuration. Use generated synthetic
   lab credentials for a reproducible test; do not enter a commercial SIM's
   authentication keys.
3. If images are missing, select **Prepare missing components** on
   **Preparation**, or **Download missing** in the scenario workspace, then
   confirm the preparation.
4. Select **Start lab** and wait for the startup checks.
5. Open **Validation** or select **Run evidence check** in the workspace. For a complete simulation
   check, review UE registration, session/bearer, tunnel/IP, and data-ping
   results. A running container by itself does not mean the UE connected.
6. If a check fails, open **Troubleshooter** for the cause and available
   recovery action. Then review the selected profile's logs before retrying.

When another scenario is active, the interface may ask whether to stop it before
starting the selected profile. Review the active scenario and confirm the switch
only if you intend to stop that run. Do not remove containers or volumes to
resolve a normal profile-switch prompt.

The command-line equivalent for 5G SA is:

```bash
./lain5g scenario setup 5g-sa
./lain5g images pull 5g-sa
./lain5g scenario start 5g-sa
./lain5g scenario status 5g-sa
./lain5g scenario validate 5g-sa
./lain5g scenario logs 5g-sa
./lain5g scenario stop 5g-sa
```

Use `4g-lte-sim` instead of `5g-sa` for the LTE software simulation. The web
interface is recommended because it keeps profile state, confirmation prompts,
validation, and logs together.

## 5. Manage subscribers

Open **Subscribers** after the packet core you want to use is running. Select
the matching core/profile in the page. If the core is stopped, a database
connection status of disconnected or timeout is expected; the Subscribers page
does not start the core automatically.

For a lab user, choose a preset:

- **Voice + data** provisions the common `internet` and `ims` services.
- **Data only** provisions `internet` only.

Use one subscriber identity and matching authentication values for the packet
core and physical test SIM. Values such as Ki and OPc are SIM-specific. Keep
them private; OpenLain5G masks them in subscriber lists. A stored subscriber
record only means the core database has that record; it does not prove that a UE
has authenticated or established service. Confirm that through a scenario's
validation evidence.

Subscriber changes require operations mode and the page's confirmation. If a
record is intended only for a demo, use synthetic credentials and remove the
record after the test through the Subscribers page.

## 6. Optional: program a physical test SIM

The **SIM Programmer** page is optional and requires a PC/SC reader prepared by
`./install.sh`. The bridge runs only in operations mode. It currently writes
sysmoUSIM-SJS1 cards; sysmoISIM-SJA2 and SJA5 are detected read-only. Use only a
test card whose ADM1 code you know. Do not guess the ADM code.

The page can inspect a card without writing. A programming operation changes
the card and must be explicitly confirmed. After it succeeds, add the same
subscriber credentials to the selected Open5GS core: SIM programming does not
create a subscriber record. See [Physical SIM programming](sim_programmer.md)
for the full supported-card workflow and encrypted backup details.

## 7. Read validation, logs, and metrics

- **Dashboard** shows current application and scenario state. Use it to see
  what is active now.
- **Validation** shows evidence from the latest check. Green results remain as
  saved evidence after a scenario stops; they do not mean the services are still
  running.
- **Logs** shows recent service output for the selected scenario. Filter by
  service, level, or text; download or copy only after checking that the output
  contains no credentials or private subscriber data.
- **Runs** keeps each execution and its validation report together.
- **Metrics** links to application-runtime and network-component dashboards.
  The runtime dashboard shows API and process metrics. Component activity and
  log error panels are derived from container logs; they are not RF or radio
  measurements.

The central Grafana/Loki log collection starts in operations mode. Prometheus
retains metrics for 15 days and Loki retains collected logs for seven days in
local Docker volumes. Keep Grafana and Prometheus on localhost.

## 8. Stop the lab

Stop the active scenario from its page or from **Dashboard**. Then stop the web
application when you are done:

```bash
./lain5g app stop
```

Stopping a scenario stops its services and preserves its run evidence and saved
validation. Stopping the application also stops its local monitoring stack and
SIM bridge. It does not delete named data volumes. Use **Dashboard** or
`./lain5g status` to check what is active rather than interpreting old green
checks as live status.

## 9. Use guarded USRP profiles

RF profiles require compatible hardware, a reviewed local channel plan, valid
authorization, an isolated or properly cabled setup, the correct attenuation,
and an accessible Emergency Stop. Verify the exact band, frequency, bandwidth,
gain, antenna/cable path, and maximum duration with the lab's responsible
operator before enabling a run. RF stays blocked unless the operator and all
profile safeguards allow it.

Start with the profile's non-transmitting hardware and preflight checks. The
hardware check can identify Ethernet, route, UHD, or FPGA problems without
starting the RAN. Use the on-page checklist and Emergency Stop for any authorized
transmission. Do not flash the USRP or change host routes based on an automatic
troubleshooter suggestion. See [RF safety](rf_safety.md) and the relevant
[X310 LTE guide](x310_lte.md) before operation.

Software simulation results and RF results have different evidence scopes. A
simulation pass does not prove RF emission or commercial UE reception. An
eNB/gNB process running does not prove that a phone registered.

## 10. Diagnose common problems

Start with these read-only checks:

```bash
./lain5g status
./lain5g doctor PROFILE
./lain5g scenario status PROFILE
./lain5g scenario validate PROFILE
./lain5g scenario logs PROFILE
```

Replace `PROFILE` with the selected profile ID. In the web interface, use
**Troubleshooter** for likely causes and supported recovery actions. It does not
fix physical cable, host-route, FPGA, SIM, or RF authorization problems.

Do not publish raw logs. Before sharing diagnostics, remove credentials, IMSIs,
phone numbers, private addresses, reader/card identifiers, and RF details.
See [Troubleshooting](troubleshooting.md) for detailed diagnosis steps.

## 11. Updates and removal

Check the available version and local project status with:

```bash
./lain5g version check
./lain5g status
```

Use the **Maintenance** menu or the documented version workflow to switch
releases. Stop active scenarios first and retain the generated backup branch.

For removal, inspect the plan before applying it:

```bash
./lain5g uninstall --scope all --dry-run
```

Normal removal preserves named volumes and local data. A complete removal with
`--purge-all` deletes OpenLain5G containers, networks, volumes, locally tagged
images, the installation log directory, and the checkout after a separate
interactive confirmation. The CLI requires the exact phrase
`BORRAR OPENLAIN5G COMPLETAMENTE`; `--yes` cannot bypass it. Back up subscriber
data and experiment results first.
See [Installation](installation.md#alternative-manual-setup) for the exact
confirmation and removal scopes.
