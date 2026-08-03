# Architecture

OpenLain5G does not implement its own 4G/5G core. It uses external components
and provides its own deployment, configuration, management, validation, and
visualization layer.

The architecture separates scenarios by directory, Compose project, network,
and volume to prevent interference between 5G SA and 4G LTE/IMS.

## 5G SA components

- MongoDB stores Open5GS data, including the lab subscriber.
- Open5GS runs NRF, AMF, SMF, UPF, AUSF, UDM, UDR, and PCF.
- UERANSIM runs the software gNB and UE.
- Docker Compose connects all services on the `lain5g-lab-5g-sa-core` network.
- `runs/` stores minimal per-run results without copying full configurations or
  code.
- `5g-sa-x310` adds compact MariaDB, P-CSCF, I-CSCF, S-CSCF, and DNS services to
  the always-on core; the gNB remains isolated in the `rf` profile. Physical-UE
  IMS registration and VoNR are handled as a separate integration and evidence
  scope.

## 4G LTE/IMS components

- Open5GS runs MME, HSS, SGW-C, SGW-U, and PCRF. Its SMF and UPF binaries provide
  the PGW control-plane and user-plane roles.
- srsRAN 4G runs the eNB and UE on the software path.
- In the compact simulation, Kamailio runs P-CSCF and I-CSCF, while the
  `ims-sip` service provides the minimal S-CSCF registrar. The USRP path uses
  Kamailio for all three roles.
- CoreDNS resolves lab IMS names.
- The X310 path isolates `enb-x310` in the `rf` Compose profile with
  `network_mode: host`.
- Its compact IMS services always start with the EPC, and their results are
  recorded for each run.
- Actual RF manifests are ignored by Git and must be created manually.

## Current limitations

- End-to-end results depend on the profile, hardware, UE, and evidence associated
  with each authorized run.
- The project does not use Kubernetes, a microservices architecture, or
  Electron.
- RF does not run without explicit authorization and preflight checks.
- The API and frontend manage 4G/5G paths within a local trust boundary. The base
  application is observation-only; mutation requires explicit opt-in and separate
  access to the Docker socket.
