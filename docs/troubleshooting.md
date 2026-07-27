# Troubleshooting

## `.env` faltante

Ejecuta:

```bash
./lain5g scenario setup 5g-sa
```

El comando crea credenciales sintéticas locales sin imprimirlas.

## Conflicto `10.20.0.3` al iniciar 5G con la web activa

MongoDB e `init-subscriber` usan `10.20.0.2` y `10.20.0.3`. El backend web debe
conectarse con la IP reservada `10.20.0.250`; las versiones anteriores podían
recibir una de esas direcciones dinámicamente y bloquear el inicio. Actualiza el repositorio y recrea el backend
con `make app-down-operations && make app-up-operations`. No es necesario
desconectarlo manualmente ni eliminar los volúmenes del escenario.

## gNB no conecta

Revisa que `deployments/5g-sa/ueransim/gnb.yaml` apunte al AMF `10.20.0.5:38412` y que `amf.yaml` use el mismo MCC, MNC y TAC.

## UE no registra

El UE renderiza IMSI, K, OPc, AMF y SQN desde `.env`. Comprueba el resultado sin
publicar secretos mediante `./lain5g scenario logs 5g-sa` y busca errores de
autenticación en `init-subscriber`, `amf`, `ausf` y `ue`. Reinicia todo el
escenario después de cambiar `.env`.

## No hay ping

Revisa que el contenedor UPF tenga `/dev/net/tun`, `NET_ADMIN`, `ogstun` y NAT activo. Ejecuta `make validate-5g-sa` para ver en qué punto falla.
