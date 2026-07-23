# 5G SA

5G SA es la prioridad inicial del proyecto.

El estado científico se mantiene en la
[tabla canónica de capacidades](../README.md#canonical-capability-status). La
[ejecución pública `run-20260723-054913`](../results/public/5g-sa-sim/run-20260723-054913.json)
registra 15/15 comprobaciones `PASS` y clasificación `SIMULATION_ONLY` para el
commit fuente `12c4a38404bbaf240c698a056e3f47182081ab5c`. El artefacto anonimizado
fue añadido por el commit posterior
`060e669d3f65e1844a702b1b5264be6933ef45c2`; ese commit publica el resultado y
no representa otra ejecución.

## Comandos

```bash
cp deployments/5g-sa/.env.example deployments/5g-sa/.env
make build-5g-sa
make start-5g-sa
make status-5g-sa
make validate-5g-sa
make logs-5g-sa
make stop-5g-sa
```

## Archivos editables

- `deployments/5g-sa/open5gs/amf.yaml`
- `deployments/5g-sa/open5gs/smf.yaml`
- `deployments/5g-sa/open5gs/upf.yaml`
- `deployments/5g-sa/ueransim/gnb.yaml`
- `deployments/5g-sa/ueransim/ue.yaml`
- `deployments/5g-sa/.env`

El perfil se puede aplicar mediante la CLI o la API para generar una
configuración coherente. Los archivos también se pueden editar manualmente, pero
no deben mezclarse ambos métodos sin revisar el diff resultante. `.env` es local
y permanece fuera de Git.

## Evidencia esperada

El resumen público reporta 15 comprobaciones aprobadas por el validador,
incluidas las siguientes. La validación software solo debe considerarse completa
para ese alcance y commit si hay evidencia correlacionada de:

- Open5GS iniciado.
- gNB conectado al AMF.
- UE registrado.
- sesión PDU establecida.
- interfaz `uesimtun0` creada.
- IP asignada al UE.
- ping exitoso desde el UE.

Contenedores activos por sí solos no validan el escenario.

La simulación UERANSIM no se extrapola a radio real. El registro, la sesión PDU
y los datos 5G SA con un UE comercial permanecen `NOT_VALIDATED`.
