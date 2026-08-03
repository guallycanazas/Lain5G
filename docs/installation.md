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
configuration; and downloads the published images. Each privileged command is
displayed before `sudo` is used.

Other distributions, rootless Docker installations, managed workstations, and
nonstandard init systems should satisfy the requirements below manually. The
installer does not override host policy when daemon or group management is not
available.

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

The console is the recommended entry point. Its first option installs missing
dependencies and downloads the complete lab; it also supports scenario
operations and launches the web application:

```bash
./lain5g
```

Select `PREPARAR MAQUINA Y DESCARGAR TODO` for a new installation,
`Imagenes y componentes` to manage downloads, `Perfiles y operacion` to
configure/start/validate/stop a network, or `Aplicacion web` to prepare, start,
open, and stop the interface. Downloading images does not build or start
services.

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

To download all published components:

```bash
./lain5g images pull all
```

The `make images-pull` and `make app-up` commands and each scenario's targets
remain available as an alternative automation interface.

## Alternative Builds

Local builds are required only when developing or modifying components:

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
`VERSION` file; use `docker build -f backend/Dockerfile .` if you need to build
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
