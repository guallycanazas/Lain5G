# VoLTE Validation

El estado actual se define en la
[tabla canónica de capacidades](../README.md#canonical-capability-status): la red
y señalización VoLTE software están validadas.

El [resultado público IMS 4G](../results/public/4g-ims-sim/run-20260723-055149.json)
del commit fuente `12c4a38404bbaf240c698a056e3f47182081ab5c` registra
22/22 comprobaciones `PASS` y está clasificado `SIMULATION_ONLY`. Cubre LTE,
EPC, bearer/APN, datos, IMS, DNS y registro SIP Digest autenticado. El
artefacto fue añadido por el commit de publicación
`060e669d3f65e1844a702b1b5264be6933ef45c2`.

## Evidencia VoLTE Validada

La validación conserva evidencia de:

- Registro LTE del UE.
- Bearer de datos y APN `ims` provisionado.
- `SIP REGISTER` exitoso.
- Logs de EPC, IMS, eNB y UE asociados al mismo `run-id`.

El diálogo `INVITE`/`ACK`/`BYE`, RTP bidireccional y las métricas de audio se
evalúan en una prueba de medios separada cuando ese alcance sea requerido.

## SIP REGISTER

Para declarar `sip_register PASS`, la validación requiere evidencia real de:

- REGISTER inicial del cliente SIP.
- Desafío `401 Unauthorized` o equivalente.
- REGISTER autenticado.
- Respuesta final `200 OK`.
- Logs correlacionados de cliente SIP, P-CSCF, I-CSCF y S-CSCF.

Encontrar solo la palabra `REGISTER` en logs no es suficiente.

## Estados De Validación

- `PASS`: evidencia encontrada.
- `FAIL`: requisito obligatorio ausente o servicio crítico caído.
- `WARNING`: evidencia parcial o no concluyente.
- `NOT_TESTED`: la prueba no aplica o no se ejecutó.

## Salidas

Las validaciones escriben JSON en `runs/<run-id>/`. Estos archivos son evidencia
operativa privada, no sustituyen una captura SIP/RTP completa y no se convierten
en evidencia pública sin anonimización, commit exacto y correlación verificable.
