# 4G LTE, IMS y Preparación VoLTE

El escenario `deployments/4g-volte` agrega una ruta 4G aislada del despliegue `5g-sa`. No reutiliza redes, volúmenes ni nombres de proyecto Compose de 5G SA.

El estado científico se mantiene únicamente en la
[tabla canónica de capacidades](../README.md#canonical-capability-status).
Esta guía describe composición y operación, no evidencia de una llamada.

Perfiles disponibles:

- `4g-lte-sim`: EPC + srsENB + srsUE por ZMQ, sin servicios IMS.
- `4g-volte-sim`: EPC + IMS + srsRAN 4G en modo software.
- `4g-lte-x310`: EPC + IMS + eNB srsRAN 4G para hardware X-Series compatible,
  con RF bloqueada por defecto. El nombre histórico del perfil se conserva.

Para el commit fuente `12c4a38404bbaf240c698a056e3f47182081ab5c`, el
[resultado LTE público](../results/public/4g-lte-sim/run-20260723-055025.json)
registra 14/14 comprobaciones `PASS` y el
[resultado IMS 4G público](../results/public/4g-ims-sim/run-20260723-055149.json)
registra 22/22. Ambos son `SIMULATION_ONLY` y fueron publicados en el commit
`060e669d3f65e1844a702b1b5264be6933ef45c2`. El segundo corresponde al perfil
`4g-volte-sim`, pero solo reporta comprobaciones de registro SIP Digest de
laboratorio, no AKA/Cx/Rx, llamada, RTP, SDR ni UE comercial.

## Alcance Actual

- EPC 4G basado en Open5GS `v2.7.5`.
- IMS mínimo con Kamailio `5.8.8` y base SQL inicial.
- Provisionamiento de APN `internet` e `ims` para un suscriptor de laboratorio.
- Validaciones estáticas, scripts operativos y workspaces guiados en la API/frontend.

## Límites

- La ruta LTE con UE comercial solo tiene marcadores privados parciales de S1,
  RRC, contexto/bearer y conexión. No existe un artefacto persistido y
  correlacionado del bearer de datos.
- No se declara llamada VoLTE completa.
- No se inicia RF sin manifiesto real, plan de canal real y autorización explícita.
- La ruta X310 no actualiza firmware ni FPGA automáticamente.

El marcador `INVITE` privado disponible no está acompañado por una respuesta
final exitosa correlacionada al `INVITE`, `ACK`, `BYE` ni RTP bidireccional. No
se declarará una llamada completa sin conservar ese diálogo y los medios bajo
el mismo run y commit. No se encontró ni se afirma un marcador `MESSAGE`.

## Preparación

```bash
cp deployments/4g-volte/common/.env.example deployments/4g-volte/common/.env
nano deployments/4g-volte/common/.env
```

Define claves de laboratorio para `SUBSCRIBER_KEY` y `SUBSCRIBER_OPC`. No uses IMSI, Ki, OPc ni MSISDN reales sin anonimizar.

## Comandos Principales

```bash
make build-4g-lte-sim
make start-4g-lte-sim
make validate-4g-lte-sim
make stop-4g-lte-sim
```

```bash
make build-4g-volte-sim
make start-4g-volte-sim
make validate-4g-volte-sim
make stop-4g-volte-sim
```

```bash
make build-4g-lte-x310
make check-x310
make preflight-4g-lte-x310
make start-4g-lte-x310-epc
```

El inicio RF real usa `make start-4g-lte-x310-rf` y está documentado en
[X310 LTE](x310_lte.md) y [seguridad RF](rf_safety.md).
