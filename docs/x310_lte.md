# X310 LTE

`4g-lte-x310` prepara un eNB LTE con srsRAN 4G y UHD para hardware USRP
X-Series compatible. El nombre histórico del perfil se conserva. El EPC e IMS
pueden iniciarse sin RF; el eNB RF está en un perfil Compose separado llamado
`rf`.

## Comandos Sin RF

```bash
make build-4g-lte-x310
make check-x310
make preflight-4g-lte-x310
make start-4g-lte-x310-epc
make status-4g-lte-x310
make stop-4g-lte-x310
```

## Inicio RF

No ejecutes RF hasta completar `docs/rf_safety.md`.

Requisitos mínimos:

- `deployments/4g-volte/x310/rf/channel-plan.yaml` creado desde el ejemplo y revisado.
- `deployments/4g-volte/x310/rf/safety-manifest.yaml` creado desde el ejemplo y con `authorization_confirmed: true`.
- `LAIN5G_ALLOW_RF_START=true` definido solo para la ejecución autorizada.
- Duración finita mediante `maximum_duration_seconds`.

Comando:

```bash
LAIN5G_ALLOW_RF_START=true make start-4g-lte-x310-rf
```

El script ejecuta preflight, arranca solo `enb-x310`, espera la duración definida y ejecuta auto-stop.

## Inicio Desde La Interfaz

Ejecute `make app-up` y abra `http://localhost:8080/scenarios/4g-lte-x310`. Use `Core only` para verificar EPC e IMS sin RF. `Start core + RF` muestra el plan de canal efectivo y exige completar las guardas antes de habilitar una ejecución real; si `Execute real RF` permanece desmarcado, la acción es un dry-run que no transmite. El botón `Emergency stop` permanece disponible en el workspace.

## Alcance de las observaciones

Una auditoría histórica no encontró las herramientas UHD del host en `PATH` y
no pudo inspeccionar hardware en esa sesión. Existen observaciones privadas
posteriores, pero no son evidencia pública ligada al candidato. Consulte la
[tabla canónica](../README.md#canonical-capability-status) en lugar de inferir
un estado actual a partir de cualquiera de esas sesiones.

La imagen UHD no actualiza FPGA ni firmware al iniciar.
