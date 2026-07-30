# 5G SA

5G SA es la prioridad inicial del proyecto.

El estado científico se mantiene en la
[tabla canónica de capacidades](../README.md#canonical-capability-status). La
[ejecución pública `run-20260730-021914`](../results/public/5g-sa-sim/run-20260730-021914.json)
registra 15/15 comprobaciones `PASS` y clasificación `SIMULATION_ONLY` para el
commit fuente `59471947da95783c1a85a4d18284360e4b6d898b`, ejecutado en una VM
Ubuntu 24.04 limpia. El resultado de julio 23 permanece como registro histórico.

## Comandos

```bash
./lain5g scenario setup 5g-sa
./lain5g images pull 5g-sa
./lain5g scenario start 5g-sa
./lain5g scenario status 5g-sa
./lain5g scenario validate 5g-sa
./lain5g scenario logs 5g-sa
./lain5g scenario stop 5g-sa
```

## Archivos editables

- `deployments/5g-sa/open5gs/amf.yaml`
- `deployments/5g-sa/open5gs/smf.yaml`
- `deployments/5g-sa/open5gs/upf.yaml`
- `deployments/5g-sa/ueransim/gnb.yaml`
- `deployments/5g-sa/ueransim/ue.yaml` (plantilla sin secretos)
- `deployments/5g-sa/.env`

El perfil se puede aplicar mediante la CLI o la API para generar una
configuración coherente. Los archivos también se pueden editar manualmente, pero
no deben mezclarse ambos métodos sin revisar el diff resultante. `.env` es local
y permanece fuera de Git.

Al iniciar, Compose renderiza una copia temporal del YAML del UE con IMSI, K,
OPc, AMF y SQN tomados de `.env`. La copia runtime no se escribe en el repositorio.

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
