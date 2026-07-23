# Troubleshooting

## `.env` faltante

Ejecuta:

```bash
cp deployments/5g-sa/.env.example deployments/5g-sa/.env
```

Después edita las claves de laboratorio.

## gNB no conecta

Revisa que `deployments/5g-sa/ueransim/gnb.yaml` apunte al AMF `10.20.0.5:38412` y que `amf.yaml` use el mismo MCC, MNC y TAC.

## UE no registra

Revisa que IMSI, K, OPc, AMF, SQN, MCC y MNC coincidan entre `.env`, `subscriber-init.js` y `ueransim/ue.yaml`.

## No hay ping

Revisa que el contenedor UPF tenga `/dev/net/tun`, `NET_ADMIN`, `ogstun` y NAT activo. Ejecuta `make validate-5g-sa` para ver en qué punto falla.
