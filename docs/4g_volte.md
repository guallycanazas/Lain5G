# Red 4G LTE y VoLTE

El escenario `deployments/4g-volte` agrega una ruta 4G aislada del despliegue `5g-sa`. No reutiliza redes, volúmenes ni nombres de proyecto Compose de 5G SA.

El estado científico se mantiene únicamente en la
[tabla canónica de capacidades](../README.md#canonical-capability-status).
Esta guía describe la composición, operación y evidencia de señalización VoLTE
del escenario software.

Perfiles disponibles:

- `4g-lte-sim`: EPC + srsENB + srsUE por ZMQ, sin servicios IMS.
- `4g-volte-sim`: EPC + IMS + srsRAN 4G en modo software.
- `4g-lte-x310`: EPC + eNB srsRAN 4G para hardware X-Series compatible,
  infraestructura IMS compacta siempre activa y RF bloqueada por defecto. El
  nombre histórico del perfil se conserva.

Para el commit fuente `12c4a38404bbaf240c698a056e3f47182081ab5c`, el
[resultado LTE público](../results/public/4g-lte-sim/run-20260723-055025.json)
registra 14/14 comprobaciones `PASS` y el
[resultado IMS 4G público](../results/public/4g-ims-sim/run-20260723-055149.json)
registra 22/22. Ambos son `SIMULATION_ONLY` y fueron publicados en el commit
`060e669d3f65e1844a702b1b5264be6933ef45c2`. El segundo corresponde al perfil
`4g-volte-sim` y valida LTE, EPC, datos, servicios IMS, DNS, provisionamiento y
registro SIP autenticado de laboratorio.

## Alcance Actual

- EPC 4G basado en Open5GS `v2.7.5`.
- IMS mínimo con Kamailio `5.8.8` y base SQL inicial.
- Provisionamiento de APN `internet` e `ims` para un suscriptor de laboratorio.
- Validaciones estáticas, scripts operativos y workspaces guiados en la API/frontend.

## Alcance de Validación

- La red VoLTE software registra 22/22 comprobaciones `PASS`.
- La evidencia incluye registro LTE, bearer/APN, conectividad, IMS y REGISTER
  autenticado hasta 200 OK.
- No se inicia RF sin manifiesto real, plan de canal real y autorización explícita.
- La ruta X310 no actualiza firmware ni FPGA automáticamente.
- En X310, la evidencia de registro IMS, señalización de llamada y medios se
  conserva por ejecución junto con los logs del operador.

Las métricas de audio, el diálogo de llamada y el rendimiento RTP se tratan como
pruebas de medios separadas y no cambian la clasificación validada de la red y
señalización VoLTE software.

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

El escenario VoLTE se conserva como implementación y evidencia histórica, pero
no forma parte de la interfaz operativa pública.

```bash
make build-4g-lte-x310
make check-x310
make preflight-4g-lte-x310
make start-4g-lte-x310-epc
```

El inicio RF real usa `make start-4g-lte-x310-rf` y está documentado en
[X310 LTE](x310_lte.md) y [seguridad RF](rf_safety.md).
