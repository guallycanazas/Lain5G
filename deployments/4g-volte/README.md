# Red 4G LTE y VoLTE

Este escenario contiene dos perfiles independientes:

- `4g-volte-sim`: red software validada con EPC, IMS, srsENB y srsUE.
- `4g-lte-x310`: ruta RF controlada con EPC, IMS y srsENB para USRP X310.

La ruta RF no se inicia automáticamente y exige preflight, manifiesto de seguridad y `LAIN5G_ALLOW_RF_START=true`.

La validación VoLTE software cubre LTE, EPC, bearer/APN, conectividad de datos,
servicios IMS, DNS, provisionamiento de suscriptor y registro SIP autenticado.
El [resultado público `run-20260723-055149`](../../results/public/4g-ims-sim/run-20260723-055149.json)
registra 22/22 comprobaciones `PASS` y clasificación `SIMULATION_ONLY`.

## Preparación

```bash
cp deployments/4g-volte/common/.env.example deployments/4g-volte/common/.env
```

Edita `deployments/4g-volte/common/.env` y usa claves de laboratorio, nunca credenciales reales.

## Simulación Software

```bash
make build-4g-volte-sim
make start-4g-volte-sim
docker compose --profile sip --env-file deployments/4g-volte/common/.env \
  -f deployments/4g-volte/sim/docker-compose.yml up --force-recreate sip-register
make validate-4g-volte-sim
make stop-4g-volte-sim
```

El paso `sip-register` comprueba el intercambio REGISTER, desafío 401, REGISTER
autenticado y respuesta final 200 OK. Junto con las comprobaciones LTE/EPC/IMS,
establece el flujo de señalización VoLTE validado en software. Audio, calidad de
voz y rendimiento RTP pertenecen a una prueba de medios separada.

## X310 Sin RF

```bash
make build-4g-lte-x310
make check-x310
make preflight-4g-lte-x310
make start-4g-lte-x310-epc
make stop-4g-lte-x310
```

## X310 Con RF

La RF requiere `safety-manifest.yaml`, `channel-plan.yaml`, `LAIN5G_ALLOW_RF_START=true`, autorización real y duración finita. Ver `docs/rf_safety.md` antes de usar `make start-4g-lte-x310-rf`.
