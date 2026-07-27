# 5G VoNR

El escenario software `5g-vonr-sim` integra 5G SA, dos DNN y un IMS de
laboratorio. Su clasificación se mantiene en la
[tabla canónica de capacidades](../README.md#canonical-capability-status).

La ejecución operacional `run-20260725-213427` completó 25/25 comprobaciones
`PASS`: 5GC, NG Setup, registro UE, sesiones PDU internet/IMS, ambas IP e
interfaces TUN, ping, servicios IMS, DNS IMS, ruta al P-CSCF y REGISTER SIP
autenticado con 401 y 200 OK. Por ello VoNR se clasifica como validado en
simulación dentro de ese alcance.

El [intento público `run-20260723-055328`](../results/public/5g-vonr-sim/run-20260723-055328.json)
se conserva como evidencia histórica del timeout inicial y no representa el
estado actual. RF, UE comerciales, audio y rendimiento RTP permanecen como
alcances de validación separados del escenario software.
