# Validation

Esta guía define criterios y salidas e indexa los artefactos públicos sin crear
una segunda matriz normativa. Consulte la
[tabla canónica de capacidades](../README.md#canonical-capability-status), que
separa evidencia pública, privada e histórica. Los resultados públicos evalúan
el commit fuente `12c4a38404bbaf240c698a056e3f47182081ab5c`; el commit posterior
`060e669d3f65e1844a702b1b5264be6933ef45c2` publica los artefactos anonimizados
sin representar una nueva ejecución.

La evidencia pública de `1.0.0-rc.1` comprende:

- [5G SA software](../results/public/5g-sa-sim/run-20260723-054913.json):
  15/15 comprobaciones `PASS`, `SIMULATION_ONLY`.
- [LTE software](../results/public/4g-lte-sim/run-20260723-055025.json):
  14/14 comprobaciones `PASS`, `SIMULATION_ONLY`.
- [IMS 4G software](../results/public/4g-ims-sim/run-20260723-055149.json):
  22/22 comprobaciones `PASS`, `SIMULATION_ONLY`; solo registro SIP Digest de
  laboratorio, sin AKA/Cx/Rx, llamada ni medios.
- [VoNR software](../results/public/5g-vonr-sim/run-20260723-055328.json):
  ejecución `BLOCKED` por timeout, `NOT_VALIDATED`, sin criterios de escenario
  evaluados. El validador alcanzó el límite de seis minutos; el intento completo
  registró 413 segundos.

La validación automática está en `deployments/5g-sa/scripts/validate.sh` y se ejecuta con:

```bash
make validate-5g-sa
```

Cada comprobación devuelve uno de estos estados:

- `PASS`
- `FAIL`
- `WARNING`
- `NOT_TESTED`

## Comprobaciones 5G SA

- MongoDB activo.
- NRF activo.
- AMF activo.
- SMF activo.
- UPF activo.
- AUSF activo.
- UDM activo.
- UDR activo.
- PCF activo.
- conexión NG entre gNB y AMF.
- registro del UE.
- establecimiento de sesión PDU.
- interfaz TUN `uesimtun0`.
- IP asignada al UE.
- ping desde el UE hacia `PING_TARGET`.

El resultado se guarda en `runs/<run-id>/validation.json`.

## Comprobaciones 4G LTE/IMS

```bash
make validate-4g-lte-sim
make validate-4g-volte-sim
make validate-4g-lte-x310
```

La ruta `4g-lte-sim` revisa EPC, marcadores S1, registro de srsUE, bearer,
interfaz UE y ping de datos sin iniciar IMS. `4g-volte-sim`, cuyo artefacto
público usa el nombre de alcance `4g-ims-sim`, añade servicios IMS, DNS y
evidencia de registro SIP de laboratorio.

La ruta X310 separa comprobaciones de hardware, UHD, FPGA, EPC, IMS, preflight RF, auto-stop y logs del eNB. En modo seco se reporta `NOT_TESTED` sin iniciar RF; ese resultado no valida una capacidad de radio.

La llamada VoLTE completa permanece `NOT_VALIDATED`: la evidencia disponible no
contiene una respuesta final exitosa correlacionada al `INVITE`, `ACK`, `BYE` ni
RTP bidireccional. Consulte los
[criterios VoLTE](volte_validation.md).
