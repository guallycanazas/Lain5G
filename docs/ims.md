# IMS

Los perfiles RF públicos incluyen infraestructura IMS compacta de laboratorio.
Se inicia junto con el núcleo, sin habilitar RF por sí sola:

- `pcscf` con Kamailio.
- `icscf` con Kamailio.
- `scscf` con Kamailio en `4g-lte-x310` y un registrador SIP mínimo con Digest
  MD5 en `5g-sa-x310`.
- `ims-database` con esquema SQL inicial.
- `dns` con CoreDNS para dominios IMS de laboratorio.

El cliente `sip-register` pertenece a los escenarios de señalización software
internos; no se ejecuta en los perfiles X310 públicos.

## Configuración

Los dominios IMS se definen en `deployments/4g-volte/common/.env`:

```bash
IMS_DOMAIN=ims.mnc001.mcc001.3gppnetwork.org
PCSCF_DOMAIN=pcscf.ims.mnc001.mcc001.3gppnetwork.org
ICSCF_DOMAIN=icscf.ims.mnc001.mcc001.3gppnetwork.org
SCSCF_DOMAIN=scscf.ims.mnc001.mcc001.3gppnetwork.org
IMS_AUTH_PASSWORD=<secreto local de laboratorio>
```

Para preparar secretos sintéticos locales sin copiarlos a Git:

```bash
./lain5g scenario setup 4g-lte-x310
./lain5g scenario setup 5g-sa-x310
```

El segundo comando usa `deployments/5g-sa-x310/.env`; su identidad IMS es
sintética y está separada de cualquier suscriptor o SIM físico.

El provisionamiento inicial vive en:

- `deployments/4g-volte/common/provisioning/ims-subscriber-init.sql`.
- `deployments/4g-volte/common/ims/database/init.sql`.
- `deployments/4g-volte/common/ims/dns/Corefile`.
- `deployments/4g-volte/common/ims/dns/ims.hosts`.

El usuario IMS se provisiona con:

- IMPI: `${SUBSCRIBER_IMSI}@${IMS_DOMAIN}`.
- IMPU: `sip:${SUBSCRIBER_MSISDN}@${IMS_DOMAIN}`.
- `auth_ha1`: hash Digest HA1, sin guardar la contraseña SIP en claro en la base de datos.

## SIP REGISTER

El cliente de prueba ejecuta un REGISTER real contra P-CSCF:

```bash
docker compose --profile sip --env-file deployments/4g-volte/common/.env \
  -f deployments/4g-volte/sim/docker-compose.yml up --force-recreate sip-register
```

La evidencia válida exige:

- REGISTER inicial.
- `401 Unauthorized` con desafío Digest.
- REGISTER autenticado.
- `200 OK` final.

## Alcance

La evidencia de REGISTER, señalización de llamada y RTP bidireccional se conserva
por ejecución; ver `docs/volte_validation.md`.

En ambos perfiles X310, correlacione los servicios compactos con los logs del
núcleo, RAN, UE y medios bajo un mismo `run-id`.
