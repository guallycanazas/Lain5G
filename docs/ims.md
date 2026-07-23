# IMS

El escenario 4G incluye un IMS mínimo para laboratorio:

- `pcscf` con Kamailio.
- `icscf` con Kamailio.
- `scscf` con un registrador SIP mínimo de laboratorio con Digest MD5.
- `ims-database` con esquema SQL inicial.
- `dns` con CoreDNS para dominios IMS de laboratorio.
- `sip-register` como cliente de prueba bajo perfil Compose `sip`.

## Configuración

Los dominios IMS se definen en `deployments/4g-volte/common/.env`:

```bash
IMS_DOMAIN=ims.mnc001.mcc001.3gppnetwork.org
PCSCF_DOMAIN=pcscf.ims.mnc001.mcc001.3gppnetwork.org
ICSCF_DOMAIN=icscf.ims.mnc001.mcc001.3gppnetwork.org
SCSCF_DOMAIN=scscf.ims.mnc001.mcc001.3gppnetwork.org
IMS_AUTH_PASSWORD=<secreto local de laboratorio>
```

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

IMS REGISTER exitoso no equivale a VoLTE completo. La validación completa requiere señalización SIP de llamada y RTP bidireccional; ver `docs/volte_validation.md`.
