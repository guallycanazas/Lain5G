# Red 5G SA y VoNR

Este directorio contiene la red software validada `5g-vonr-sim`, que integra
Open5GS 5GC, UERANSIM gNB/UE, DNN de internet e IMS, DNS IMS y P/I/S-CSCF. El
estado científico se mantiene en la
[tabla canónica de capacidades](../../README.md#canonical-capability-status).

La ejecución operacional `run-20260725-213427` completó 25/25 comprobaciones
`PASS`: servicios 5GC, NG Setup, registro UE, sesiones PDU de internet e IMS,
direcciones e interfaces TUN para ambos DNN, ping de datos, base IMS, P-CSCF,
I-CSCF, S-CSCF, DNS IMS, acceso al P-CSCF a través del túnel IMS y REGISTER SIP
autenticado con desafío 401 y respuesta final 200 OK.

El [artefacto público anterior `run-20260723-055328`](../../results/public/5g-vonr-sim/run-20260723-055328.json)
conserva el primer intento bloqueado como evidencia histórica y no describe el
estado operacional actual. La clasificación vigente del escenario software es
VoNR validado en simulación. RF, UE comerciales, audio y rendimiento RTP son
alcances experimentales separados.

## Operación

```bash
./deployments/5g-vonr/scripts/start.sh
./deployments/5g-vonr/scripts/validate.sh
./deployments/5g-vonr/scripts/stop.sh
```
