# 5G VoNR

Existe empaquetado para el escenario software `5g-vonr-sim`, con 5G SA e IMS de
laboratorio. Su clasificación se mantiene únicamente en la
[tabla canónica de capacidades](../README.md#canonical-capability-status). El
[intento público `run-20260723-055328`](../results/public/5g-vonr-sim/run-20260723-055328.json)
para el commit fuente `12c4a38404bbaf240c698a056e3f47182081ab5c` quedó
`BLOCKED` por timeout: el validador alcanzó el límite de auditoría de seis
minutos y no evaluó ningún criterio de escenario. El artefacto registra 413
segundos para el intento completo. Por ello su clasificación es
`NOT_VALIDATED`, no `SIMULATION_ONLY`. El artefacto fue publicado en
`060e669d3f65e1844a702b1b5264be6933ef45c2`.

Las ejecuciones históricas privadas con procedencia ausente o incompatible no
elevan esa clasificación.

El escenario software no demuestra voz ni radio real. VoNR sobre RF permanece
`NOT_VALIDATED`: faltan registro 5G SA e IMS de un UE comercial, respuesta final
exitosa al `INVITE`, `ACK`, `BYE` y RTP bidireccional correlacionados.
