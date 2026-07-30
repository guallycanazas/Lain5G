# Validation

Esta guía define criterios y salidas e indexa los artefactos públicos sin crear
una segunda matriz normativa. Consulte la
[tabla canónica de capacidades](../README.md#canonical-capability-status), que
separa evidencia pública, privada e histórica. Los resultados actuales de LTE y
5G SA evalúan el commit fuente `59471947da95783c1a85a4d18284360e4b6d898b`
en una VM Ubuntu 24.04 limpia. Los artefactos de julio 23 conservan su commit y
versión pre-release históricos.

La evidencia pública para la línea estable `1.1.0` comprende:

- [5G SA software](../results/public/5g-sa-sim/run-20260730-021914.json):
  15/15 comprobaciones `PASS`, `SIMULATION_ONLY`.
- [LTE software](../results/public/4g-lte-sim/run-20260730-021702.json):
  14/14 comprobaciones `PASS`, `SIMULATION_ONLY`.
- [VoLTE/IMS 4G software](../results/public/4g-ims-sim/run-20260723-055149.json):
  resultado histórico con 22/22 comprobaciones `PASS`, `SIMULATION_ONLY`;
  valida LTE, EPC, IMS, datos y registro SIP autenticado de laboratorio.
- [VoNR software](../results/public/5g-vonr-sim/run-20260723-055328.json):
  intento `BLOCKED` y `NOT_VALIDATED`; una ejecución local posterior fue
  reportada con 25/25, pero no tiene artefacto público revisable.

La validación automática está en `deployments/5g-sa/scripts/validate.sh` y se ejecuta con:

```bash
make validate-5g-sa
```

Cada comprobación devuelve uno de estos estados:

- `PASS`
- `FAIL`
- `WARNING`
- `NOT_TESTED`

La aplicación agrupa esas comprobaciones en una cadena visual de evidencia. En
simulación, las etapas son core, enlace RAN, registro/sesión UE, interfaz/IP y
ping enlazado al túnel UE. Una etapa solo aparece verde cuando todos sus checks
requeridos tienen evidencia `PASS`; un contenedor activo no se interpreta como
registro UE ni tráfico de usuario. El estado global también se deriva de los
checks y no confía en un `PASS` grabado por un script antiguo.

En perfiles X310, la cadena separa detección UHD, preflight, core, proceso RAN,
enlace S1/NG y prueba UE por aire. La ejecución del eNB/gNB no demuestra por sí
sola emisión o recepción RF. La etapa UE permanece `NOT_TESTED` hasta disponer
de evidencia correlacionada de un equipo externo durante la sesión autorizada.

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

## Comprobaciones 4G LTE

```bash
make validate-4g-lte-sim
make validate-4g-lte-x310
```

La ruta `4g-lte-sim` revisa EPC, marcadores S1, registro de srsUE, bearer,
interfaz UE y ping de datos sin iniciar IMS. La evidencia histórica `4g-volte-sim`, cuyo artefacto
público usa el nombre de alcance `4g-ims-sim`, añade servicios IMS, DNS y
evidencia de registro SIP de laboratorio.

La ruta X310 separa comprobaciones de hardware, UHD, FPGA, EPC, disponibilidad
de infraestructura IMS, preflight RF, auto-stop y logs del eNB. La evidencia
extremo a extremo adicional se conserva bajo el `run-id` del operador. En modo
seco no se inicia RF.

`5g-sa-x310` registra igualmente su evidencia local y logs correlacionados en
`runs/`.

La validación VoLTE vigente cubre registro LTE, bearer/APN, datos, servicios IMS,
DNS y el intercambio REGISTER autenticado hasta 200 OK. Los criterios de audio,
diálogo de llamada y rendimiento RTP se gestionan como pruebas de medios
separadas; consulte [criterios VoLTE](volte_validation.md).
