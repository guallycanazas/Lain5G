# 5G SA X310 COTS UE Checklist

Use este checklist antes de cualquier transmisión RF con `5g-sa-x310`. No registre valores reales de IMSI, K, OPc, Ki, AMF, SQN ni contraseñas en Git.

## Equipo

- Celular compatible con 5G SA standalone, no solo NSA.
- Banda NR compatible con el celular, el hardware X-Series, las daughterboards
  instaladas y la autorización local.
- USRP X300/X310 compatible conectado por Ethernet y detectado por UHD 4.10.0.0.
- Atenuadores/cables/cámara shielded según el manifiesto de seguridad local.
- Wi-Fi del celular desactivado durante la prueba.

## SIM y suscriptor

- SIM programable configurada con MCC/MNC coincidentes con `001/01` o con el PLMN local autorizado.
- IMSI/SUPI, K/Ki, OPc, AMF y SQN coinciden con el suscriptor en Open5GS.
- No guardar IMSI real ni claves en logs compartidos; redactar identificadores antes de reportar.
- Roaming habilitado si el PLMN de laboratorio no coincide con el perfil esperado por el teléfono.
- APN `internet` configurado en el celular.
- Suscriptor Open5GS presente antes de iniciar RF.
- SUCI/SUPI revisado en logs AMF con identificadores redactados.

## Radio

- Modo 5G SA disponible y seleccionado en el celular.
- Selección manual de red disponible para el PLMN del laboratorio.
- `DL_ARFCN`, `NR_BAND`, `TX_GAIN` y `RX_GAIN` completados solo con valores autorizados localmente.
- `rf/channel-plan.yaml` creado desde el ejemplo y validado por el operador.
- `rf/safety-manifest.yaml` creado desde el ejemplo con `authorization_confirmed: true`, duración finita, `auto_stop: true` y nota de operador.

## Logs mínimos

- AMF: `SERVICE=amf make logs-5g-x310`.
- gNB: `SERVICE=gnb-x310 make logs-5g-x310` o `deployments/5g-sa-x310/gnb/.runtime/gnb-x310.log`.
- Registrar evidencia de NG Setup, Registration Request/Accept y PDU session sin exponer claves ni IMSI completo.

## Flujo seguro

- Ejecutar `make check-5g-x310`.
- Ejecutar `make preflight-5g-x310`.
- Ejecutar `make dry-run-5g-x310`.
- Iniciar core con `make start-5g-x310-core`.
- No ejecutar `make start-5g-x310-rf` hasta contar con autorización local y `LAIN5G_ALLOW_5G_RF_START=true` en el entorno del operador.
- Alternativamente, ejecutar `make app-up` y abrir `http://localhost:8080/scenarios/5g-sa-x310`; `Core only` no transmite y `Start core + RF` permanece en dry-run salvo que el operador complete todas las guardas y seleccione explícitamente `Execute real RF`.
