# Lain5G-Lab Backend

Backend FastAPI para preparar, operar y validar las redes de laboratorio 4G
LTE/VoLTE y 5G SA/VoNR, junto con los perfiles RF controlados X-Series y el
perfil NSA experimental. La API reutiliza los scripts versionados de cada
escenario bajo `deployments/` y conserva sus límites de seguridad.

## Desarrollo

```bash
make backend-install
make backend-dev
```

## Pruebas

```bash
make backend-test
make backend-cov
```

La API no inicia Docker durante el arranque. Las operaciones reales se ejecutan solo al llamar endpoints de despliegue.

## Suscriptores Open5GS

El backend expone `/api/subscribers` para administrar documentos de suscriptor en MongoDB de Open5GS usando `pymongo`.

Variables relevantes:

```env
LAIN5G_OPEN5GS_MONGO_URI=mongodb://mongo:27017/open5gs
LAIN5G_OPEN5GS_MONGO_DATABASE=open5gs
LAIN5G_OPEN5GS_SUBSCRIBER_COLLECTION=subscribers
LAIN5G_SUBSCRIBER_SECRETS_VISIBLE=false
LAIN5G_SUBSCRIBER_OPERATION_TIMEOUT=15
LAIN5G_OPEN5GS_DOCKER_NETWORK=lain5g-lab-5g-sa-core
LAIN5G_OPEN5GS_DOCKER_IP=10.20.0.250
```

Los endpoints no devuelven K, OP ni OPc completos. Ver `docs/subscribers.md`.
