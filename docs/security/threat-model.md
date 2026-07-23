# Local Backend Threat Model

## Scope

This model covers the FastAPI backend, its local web UI, project files reached
through `LAIN5G_PROJECT_ROOT`, Docker CLI calls, Open5GS subscriber access, and
the optional host Docker socket. It assumes one trusted laboratory operator on
a single workstation. It is not a multi-user or remotely exposed control
plane.

RF safety is a separate control domain. The backend mutation gate never
replaces spectrum authorization, shielding or attenuation checks, operator
acknowledgements, confirmation phrases, duration limits, or emergency-stop
procedures.

## Assets

- Host Docker control and containers.
- Writable deployment and profile configuration.
- Subscriber records and authentication material.
- Real IMS runtime credentials and state.
- RF configuration, authorization records, and operational logs.
- Run evidence that may contain infrastructure or subscriber metadata.

## Trust Boundary

The supported boundary is a loopback-only API and UI used by a trusted local
operator. `docker-compose.app.yml` fixes both published ports to `127.0.0.1`,
and the native development command also binds Uvicorn to `127.0.0.1`.
Uvicorn listens on `0.0.0.0` only inside its container so the separate frontend
container can reach it; Docker publishes that port to host loopback only.

Loopback binding and CORS are exposure reductions, not authentication. A local
process, browser exploit, malicious extension, or other user on the workstation
may still reach a loopback service. Do not enable mutations on a shared or
untrusted host, and do not publish the ports on a LAN or public interface.

## Threats And Controls

| Threat | Control | Residual risk |
| --- | --- | --- |
| Accidental or drive-by writes | `LAIN5G_MUTATING_OPERATIONS_ENABLED=false` by default; write routes return `403` | The setting is a coarse operator interlock, not user authentication |
| RF execution enabled by the general gate | `LAIN5G_RF_WEB_CONTROL_ENABLED` remains independent and defaults false; request and profile RF guards still apply | Host compromise can bypass application controls |
| Arbitrary process execution | Fixed executable and Docker-subcommand allowlists, fixed scenario/action registries, `shell=False` | An allowlisted Docker operation is powerful when the socket is present |
| Path traversal or symlink escape | Project-root resolution and confinement for scripts, working directories, Compose paths, profiles, backups, and real IMS state | A process that can rewrite the backend itself is outside this boundary |
| Shell or log injection through input | Structured Pydantic validation, control-character rejection, argument arrays, no shell parsing | Downstream tools may still interpret their own configuration formats |
| Secret or identifier leakage in command output | Key/value, URI credential, SIP identity, subscriber identifier, RF value, and note redaction; output truncation | Redaction is best effort and cannot recognize every free-form secret |
| Unbounded API log retrieval | Command output is capped by `LAIN5G_MAX_OUTPUT_CHARS`, with a hard setting maximum of 50,000 characters | Docker still produces the full captured process output before response truncation |
| Read endpoint mutates Docker networking | Automatic Open5GS network attachment is skipped unless the mutation gate is enabled | With the gate and socket enabled, a subscriber read may attach the backend network |
| Unnecessary Docker authority | Base Compose has no socket and mounts the project read-only; a separate override grants both capabilities | The override deliberately grants broad host authority |

## Mutation Policy

The general mutation setting is required for profile update/apply/restore,
non-dry-run deployment commands, image pulls, real IMS image build/start/stop
and provisioning with `execute=true`, and subscriber create/update/clone/delete
outside dry-run. Read routes, validation-only routes, real IMS plans with
`execute=false`, and deployment/subscriber dry-run behavior remain available.

Image pulls additionally require `LAIN5G_IMAGE_PULL_ENABLED=true`. RF execution
additionally requires `LAIN5G_RF_WEB_CONTROL_ENABLED=true` and all existing RF
guards. These settings are deliberately not aliases for one another.

## Docker Socket Risk

Access to `/var/run/docker.sock` is effectively root-equivalent host control.
A process with socket access can start privileged containers, mount host paths,
read host files, change networks, and replace workloads. Mounting the socket
read-only does not meaningfully restrict Docker API operations, so the project
does not describe a read-only socket mount as a security boundary.

The application allowlists reduce accidental command injection but cannot make
the Docker socket safe against a compromised backend. Use the operations
override only for the shortest necessary period on a dedicated trusted host.

## Out Of Scope

- Enterprise identity, roles, SSO, and remote multi-user access.
- Protection after host, Docker daemon, backend container, or repository write
  access is compromised.
- Secret storage, key rotation, and Git history remediation identified in the
  security audit.
- RF licensing or physical-laboratory authorization.

See `docs/security/local-deployment.md` for the supported deployment modes.
