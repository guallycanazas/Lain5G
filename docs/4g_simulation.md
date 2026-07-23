# 4G Software Simulation

Hay dos rutas 4G software independientes:

- `4g-lte-sim`: Open5GS EPC, srsENB y srsUE conectados por ZMQ, sin IMS.
- `4g-volte-sim`: el mismo alcance LTE más IMS mínimo y señalización SIP.

## Uso

```bash
cp deployments/4g-volte/common/.env.example deployments/4g-volte/common/.env
nano deployments/4g-volte/common/.env
make build-4g-lte-sim
make start-4g-lte-sim
make status-4g-lte-sim
make validate-4g-lte-sim
make logs-4g-lte-sim
make stop-4g-lte-sim
```

Para LTE + VoLTE:

```bash
make build-4g-volte-sim
make start-4g-volte-sim
make status-4g-volte-sim
make validate-4g-volte-sim
make logs-4g-volte-sim
make stop-4g-volte-sim
```

## Validación

`make validate-4g-lte-sim` revisa servicios EPC, S1 Setup, attach de srsUE, bearer predeterminado, interfaz TUN, IP y ping de datos. No inicia ni valida componentes IMS.

`make validate-4g-volte-sim` revisa servicios EPC, servicios IMS, evidencia S1, registro UE, bearer, interfaz UE, ping de datos y evidencia SIP si existe.

Estados posibles: `PASS`, `FAIL`, `WARNING`, `NOT_TESTED`.

El resultado se guarda en `runs/<run-id>/validation.json`.

## Notas

- `pgwc` y `pgwu` son nombres de servicio Compose. En Open5GS `v2.7.5` ejecutan `open5gs-smfd` y `open5gs-upfd` porque esa versión no instala binarios `open5gs-pgwcd` ni `open5gs-pgwud`.
- `4g-lte-sim` usa proyecto, red `10.43.0.0/24`, volumen y nombres de contenedor propios; el backend impide ejecutarlo al mismo tiempo que `4g-volte-sim`.
- El IMS incluido es mínimo para laboratorio y no implica VoLTE completo por sí solo.
- Si se detiene el escenario, los contenedores de 4G se paran sin tocar `5g-sa`.
