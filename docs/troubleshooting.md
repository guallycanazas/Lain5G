# Troubleshooting

## `.env` faltante

Ejecuta:

```bash
./lain5g scenario setup 5g-sa
```

El comando crea credenciales sintéticas locales sin imprimirlas.

## gNB no conecta

Revisa que `deployments/5g-sa/ueransim/gnb.yaml` apunte al AMF `10.20.0.5:38412` y que `amf.yaml` use el mismo MCC, MNC y TAC.

## UE no registra

El UE renderiza IMSI, K, OPc, AMF y SQN desde `.env`. Comprueba el resultado sin
publicar secretos mediante `./lain5g scenario logs 5g-sa` y busca errores de
autenticación en `init-subscriber`, `amf`, `ausf` y `ue`. Reinicia todo el
escenario después de cambiar `.env`.

## No hay ping

Revisa que el contenedor UPF tenga `/dev/net/tun`, `NET_ADMIN`, `ogstun` y NAT activo. Ejecuta `make validate-5g-sa` para ver en qué punto falla.
