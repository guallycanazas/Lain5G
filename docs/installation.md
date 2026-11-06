# Installation

## Automated Installation

Obtain the source with Git or a repository archive. Git is therefore a bootstrap
prerequisite when using `git clone`. From the repository root, run:

```bash
./install.sh
```

The installer supports package-manager families based on `apt-get`, `dnf`,
`pacman`, or `zypper`. It installs missing Python, Node.js, Git, Make, Docker,
Compose, and util-linux prerequisites; conditionally starts the Docker daemon or
configures group access when that model applies; generates private
configuration; downloads published images and builds the SIP test tool locally.
Each privileged command is
displayed before `sudo` is used.

At completion, the CLI prints an installation summary with the detected host
type, package manager, dependencies ensured, Docker image counts, Docker access,
and elapsed time. `install.sh` also saves the full terminal transcript with
permissions restricted to the current user at
`${XDG_STATE_HOME:-~/.local/state}/lain5g/install-<UTC timestamp>.log` and
prints its exact path. A successful report means the prerequisites and images
were prepared; it does not mean that a network scenario has been started or
validated. A dry run labels planned work and does not claim it was installed.

Other distributions, rootless Docker installations, managed workstations, and
nonstandard init systems should satisfy the requirements below manually. The
installer does not override host policy when daemon or group management is not
available.

The application source is located under `src/backend/` and `src/frontend/`.
Release metadata, operational deployments, scripts, documentation, and public
results remain at the repository root.

To review all actions without modifying the system:

```bash
./install.sh --dry-run
```

If the installer added the user to the Docker group, run `newgrp docker` or log
in again before opening the application.

## Operational Requirements

- Docker with Compose v2 support.
- The util-linux `flock` utility for mutual exclusion between RF sessions.
- A kernel with SCTP support and `/dev/net/tun` available.
- Internet access to clone and build Open5GS and UERANSIM during `make build-5g-sa`.
- For compatible X-Series USRP hardware: a suitable host network and host UHD
  tools when hardware must be validated outside the container.

## Alternative Manual Setup

Before running repository commands, install Git, Python with `venv`, Node.js,
npm, GNU Make, util-linux, Docker Engine, and Docker Compose v2 using the method
appropriate for the host. Confirm that the current user can access Docker, then
verify that the version and lock files are consistent:

```bash
make version-check
```

The web application is the recommended operational entry point. On a trusted
laboratory workstation, start it with:

```bash
./lain5g app start --operations --open
```

For observation-only access, use `./lain5g app start --open`. The second
supported entry point is the guided interactive CLI:

```bash
./lain5g
```

Use its menus to prepare the machine, manage components, select profiles, and
operate software networks. Preparation downloads pinned runtime images and
builds the small SIP test tool from the checked-in `images/ims-sip/` Dockerfile;
it does not start laboratory services.

Use `./lain5g status` for a read-only summary of the checkout, Docker daemon,
and currently running OpenLain5G containers.

The maintenance menu (`./lain5g manager`) can check stable tags and manage the
checkout version. Version changes require a clean Git worktree and stopped
OpenLain5G containers. The CLI creates a local backup branch before switching
to an exact stable tag; it does not install packages, pull profile images, or
start services automatically:

```bash
./lain5g version
./lain5g version check
./lain5g version list
./lain5g version use v1.1.8 --dry-run
./lain5g version use v1.1.8
./lain5g version rollback
```

`version use` leaves Git on the selected release tag (detached HEAD) and prints
the backup branch name. If you switch to an older release that does not include
the CLI rollback command, return with `git -C /path/to/Lain5G switch <backup>`.

To stop or remove the web application and laboratory profiles, use the staged
uninstaller. Its normal scopes remove only the selected Compose containers and
networks; they keep named volumes, images, local configuration, run reports,
the source checkout, and Docker. An active RF marker blocks removal until the
operator stops the transmission with Emergency Stop.

```bash
./lain5g uninstall --scope app --dry-run
./lain5g uninstall --scope app
./lain5g uninstall --scope 5g-sa --dry-run
./lain5g uninstall --scope ims-real --dry-run
./lain5g uninstall --scope all --dry-run
./lain5g uninstall --scope all
./lain5g uninstall --scope all --purge-all --dry-run
```

The scope can be `app`, `ims-real`, a profile ID, or `all`. For unattended
container stops, add `--yes`; this does not enable volume deletion.

To erase subscriber and monitoring data without deleting the checkout, add
`--purge-data`. The CLI lists only volumes labeled with the selected
OpenLain5G Compose project and requires the exact interactive confirmation
`DELETE OPENLAIN5G DATA`.

For a complete OpenLain5G removal, run:

```bash
./lain5g uninstall --scope all --purge-all
```

It previews the paths and project-labeled Docker volumes, then requires an
interactive terminal and the exact phrase `BORRAR OPENLAIN5G COMPLETAMENTE`;
`--yes` cannot bypass this confirmation. It removes all
OpenLain5G Compose containers, networks, labeled volumes, locally tagged
`lain5g-lab/*` and `lain5g/open5gs-webui` images, the standard installation
log directory, and the entire checkout, including local changes. Docker itself,
shared base images, host packages, unrelated containers, networks, volumes,
and images are retained. A dry run lists the plan without deleting anything.
Back up any configuration or experiment data you need first.

Use `--yes` only to approve a normal container stop in a non-interactive
session; it never bypasses either data-deletion confirmation.

The CLI automatically prepares `.env.app` with the absolute repository path.
To start the interface in safe observation mode:

```bash
./lain5g app start --open
```

To allow downloads and software-scenario operations from the application:

```bash
./lain5g app start --operations --open
```

This mode explicitly mounts the Docker socket and enables local writes and
protected RF control. Use it only on a trusted lab workstation. The interface
allows the user to select software or RF profiles for 4G/5G. Simulations
automatically prepare private synthetic credentials; RF also requires preflight
checks, authorization, a checklist, the exact confirmation phrase, a finite
duration, and an emergency stop. While an RF session is active, the CLI refuses
to stop or downgrade the application so that the web emergency stop remains
available.

The preparation page is available at:

```text
http://localhost:8080/preparation
```

A profile can also be prepared directly:

```bash
./lain5g doctor 4g-lte-sim
./lain5g images pull 4g-lte-sim
./lain5g scenario start 4g-lte-sim
./lain5g scenario validate 4g-lte-sim
./lain5g scenario stop 4g-lte-sim
```

To prepare all components:

```bash
./lain5g images pull all
```

The `make images-pull` and `make app-up` commands and each scenario's targets
remain available as an alternative automation interface.

## Alternative Builds

The SIP virtual-phone test tool is built from the checked-in Dockerfile during
Preparation so it matches the scripts in the clone. Other local component
builds are needed only when developing or modifying components:

```bash
make build-5g-sa
```

For software-based 4G:

```bash
make build-4g-lte-sim
```

For 4G with a USRP:

```bash
make build-4g-lte-x310
```

The X310 image builds UHD and can take considerably longer than the software path.

The containerized API is built from the root context to include the authoritative
`VERSION` file; use `docker build -f src/backend/Dockerfile .` if you need to build
it outside Compose.

This creates the same local tags as the automatic download:

- `lain5g-lab/open5gs:local`
- `lain5g-lab/ueransim:local`
- `lain5g-lab/srsran4g-sim:local`
- `lain5g-lab/srsran4g-uhd:local`

The local images are built from the repositories and revisions pinned in the
project Dockerfiles.

## Initial Configuration

The operational web interface and interactive console automatically prepare the
selected software scenario. To prepare a profile directly without starting
services:

```bash
./lain5g scenario setup PERFIL
```

`PERFIL` can be `4g-lte-sim`, `5g-sa`, `4g-lte-x310`, or `5g-sa-x310`. The
command generates random synthetic values in an ignored local file and applies
`0600` permissions.

To configure the values manually:

```bash
cp deployments/5g-sa/.env.example deployments/5g-sa/.env
```

Edit `deployments/5g-sa/.env` with an editor of your choice.

Set `SUBSCRIBER_KEY` and `SUBSCRIBER_OPC` to 32-character hexadecimal lab values. Do not use real keys.

For 4G:

```bash
cp deployments/4g-volte/common/.env.example deployments/4g-volte/common/.env
```

Edit `deployments/4g-volte/common/.env` with an editor of your choice.

The actual RF files `channel-plan.yaml` and `safety-manifest.yaml` are not version-controlled; see `docs/rf_safety.md`.
