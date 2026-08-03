# IMS

The public RF profiles include compact lab IMS infrastructure.
It starts alongside the core without enabling RF by itself:

- `pcscf` with Kamailio.
- `icscf` with Kamailio.
- `scscf` with Kamailio in `4g-lte-x310` and a minimal SIP registrar using
  Digest authentication with MD5 in `5g-sa-x310`.
- `ims-database` with an initial SQL schema.
- `dns` with CoreDNS for lab IMS domains.

The `sip-register` client belongs to the internal software signaling scenarios;
it does not run in the public USRP profiles.

## Configuration

The IMS domains are defined in `deployments/4g-volte/common/.env`:

```bash
IMS_DOMAIN=ims.mnc001.mcc001.3gppnetwork.org
PCSCF_DOMAIN=pcscf.ims.mnc001.mcc001.3gppnetwork.org
ICSCF_DOMAIN=icscf.ims.mnc001.mcc001.3gppnetwork.org
SCSCF_DOMAIN=scscf.ims.mnc001.mcc001.3gppnetwork.org
IMS_AUTH_PASSWORD=<local laboratory secret>
```

To prepare local synthetic secrets without copying them to Git:

```bash
./lain5g scenario setup 4g-lte-x310
./lain5g scenario setup 5g-sa-x310
```

The second command uses `deployments/5g-sa-x310/.env`; its IMS identity is
synthetic and separate from any physical subscriber or SIM.

The initial provisioning is located in:

- `deployments/4g-volte/common/provisioning/ims-subscriber-init.sql`.
- `deployments/4g-volte/common/ims/database/init.sql`.
- `deployments/4g-volte/common/ims/dns/Corefile`.
- `deployments/4g-volte/common/ims/dns/ims.hosts`.

The IMS user is provisioned with:

- IMPI: `${SUBSCRIBER_IMSI}@${IMS_DOMAIN}`.
- IMPU: `sip:${SUBSCRIBER_MSISDN}@${IMS_DOMAIN}`.
- `auth_ha1`: Digest HA1 hash, without storing the plaintext SIP password in the database.

## SIP REGISTER

The test client sends an actual REGISTER to the P-CSCF:

```bash
docker compose --profile sip --env-file deployments/4g-volte/common/.env \
  -f deployments/4g-volte/sim/docker-compose.yml up --force-recreate sip-register
```

Valid evidence requires:

- Initial REGISTER.
- `401 Unauthorized` with a Digest challenge.
- Authenticated REGISTER.
- Final `200 OK`.

## Scope

Current software validation retains REGISTER evidence. Call signaling and
bidirectional RTP require separate media-test evidence; see
`docs/volte_validation.md`.

For `4g-lte-x310`, correlate separately collected IMS evidence with core, RAN,
UE, and media logs under the same `run-id`. The `5g-sa-x310` profile has no IMS
DNN and does not establish IMS registration or VoNR.
