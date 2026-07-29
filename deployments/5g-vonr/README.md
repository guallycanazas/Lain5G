# Red 5G SA y VoNR

Este directorio conserva la implementación interna `5g-vonr-sim`, que integra
Open5GS 5GC, UERANSIM gNB/UE, DNN de internet e IMS, DNS IMS y P/I/S-CSCF. El
estado científico se mantiene en la
[tabla canónica de capacidades](../../README.md#canonical-capability-status).

Una ejecución local `run-20260725-213427` fue reportada con 25/25 comprobaciones
`PASS`, pero no existe un artefacto público para revisarla independientemente.

El [artefacto público anterior `run-20260723-055328`](../../results/public/5g-vonr-sim/run-20260723-055328.json)
es la única evidencia pública disponible y permanece `BLOCKED` y
`NOT_VALIDATED`. Este escenario no está en el catálogo operacional público
actual. RF, UE comerciales, audio y rendimiento RTP no están validados
públicamente.

## Operación

```bash
./deployments/5g-vonr/scripts/start.sh
./deployments/5g-vonr/scripts/validate.sh
./deployments/5g-vonr/scripts/stop.sh
```
