# 5G SA con VoNR

Este directorio contiene el empaquetado del escenario software `5g-vonr-sim`
con 5G SA e IMS de laboratorio. El estado científico se mantiene únicamente en
la [tabla canónica de capacidades](../../README.md#canonical-capability-status).

El [intento público `run-20260723-055328`](../../results/public/5g-vonr-sim/run-20260723-055328.json)
del commit fuente `12c4a38404bbaf240c698a056e3f47182081ab5c` quedó
`BLOCKED` por timeout y `NOT_VALIDATED`; el validador alcanzó el límite de seis
minutos y no evaluó ningún criterio de escenario. El artefacto mide 413 segundos
para el intento completo. El commit
`060e669d3f65e1844a702b1b5264be6933ef45c2` publica el artefacto anonimizado,
no una ejecución distinta.

El empaquetado no demuestra una llamada VoNR ni radio real. VoNR sobre RF
permanece `NOT_VALIDATED` hasta conservar registro de UE comercial, respuesta
final exitosa al `INVITE`, `ACK`, `BYE` y RTP bidireccional correlacionados.
