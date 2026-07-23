# Gestión de Suscriptores Open5GS

Lain5G-Lab administra documentos de suscriptores compatibles con Open5GS. No implementa el algoritmo de autenticación 5G ni sustituye las funciones AUSF, UDM o UDR.

## Arquitectura

La interfaz React consume únicamente la API FastAPI:

```text
React /subscribers
  -> Nginx /api
  -> FastAPI /api/subscribers
  -> pymongo
  -> MongoDB de Open5GS
```

MongoDB no se expone al navegador. No se aceptan consultas MongoDB arbitrarias ni nombres de colecciones desde la UI.

## Conexión a MongoDB

El backend usa estas variables:

```env
LAIN5G_OPEN5GS_MONGO_URI=mongodb://mongo:27017/open5gs
LAIN5G_OPEN5GS_MONGO_DATABASE=open5gs
LAIN5G_OPEN5GS_SUBSCRIBER_COLLECTION=subscribers
LAIN5G_SUBSCRIBER_SECRETS_VISIBLE=false
LAIN5G_SUBSCRIBER_OPERATION_TIMEOUT=15
LAIN5G_OPEN5GS_DOCKER_NETWORK=lain5g-lab-5g-sa-core
LAIN5G_MUTATING_OPERATIONS_ENABLED=false
```

Cuando el laboratorio 5G SA está detenido, la aplicación sigue iniciando y `/api/subscribers/connection` devuelve `disconnected` o `timeout` de forma controlada.

Cuando MongoDB está activo, el backend puede conectarse a la red Docker `lain5g-lab-5g-sa-core` solo si las mutaciones están habilitadas. No se levanta 5G SA automáticamente.

## Esquema Soportado

El esquema deriva de `deployments/5g-sa/mongo/subscriber-init.js`:

- `imsi`
- `msisdn`, opcional
- `security.k`
- `security.op`
- `security.opc`
- `security.amf`
- `security.sqn`
- `slice[0].sst`
- `slice[0].sd`
- `slice[0].session[0].name` como DNN

Los campos Open5GS de AMBR, QoS, `schema_version`, `subscriber_status`, `network_access_mode` y `access_restriction_data` se generan con los valores del despliegue base.

## Validaciones

- IMSI: obligatorio, solo dígitos, 5 a 15 caracteres, único.
- MSISDN: opcional, solo dígitos, 5 a 20 caracteres.
- K, OP y OPc: hexadecimales de 32 caracteres.
- Se acepta K con OP o K con OPc; no se acepta OP y OPc simultáneamente.
- AMF: hexadecimal de 4 caracteres.
- SQN: hexadecimal de 12 caracteres, conserva ceros a la izquierda.
- SST: entero entre 1 y 255.
- SD: hexadecimal de 6 caracteres.
- DNN: nombre seguro sin espacios. El despliegue base usa `internet`; `ims` queda reservado para etapas IMS futuras.

## Redacción de Secretos

Los endpoints de listado y detalle nunca devuelven `security.k`, `security.op` ni `security.opc` completos. Devuelven indicadores:

```json
{
  "k_configured": true,
  "op_configured": false,
  "opc_configured": true,
  "amf": "8000",
  "sqn": "************"
}
```

En edición, dejar K, OP u OPc vacío conserva el valor actual. Cadenas enmascaradas como `********` o `[REDACTED]` se rechazan como nuevos secretos.

## Endpoints

- `GET /api/subscribers/connection`
- `GET /api/subscribers?limit=50&offset=0&search=00101`
- `GET /api/subscribers/{imsi}`
- `POST /api/subscribers/validate`
- `POST /api/subscribers`
- `PATCH /api/subscribers/{imsi}`
- `POST /api/subscribers/{imsi}/clone`
- `DELETE /api/subscribers/{imsi}` con body `{"confirm": true}`

## Operaciones

Crear, editar, clonar y eliminar modifican directamente MongoDB de Open5GS solo cuando `LAIN5G_DRY_RUN=false` y `LAIN5G_MUTATING_OPERATIONS_ENABLED=true`. No reinician el laboratorio ni desconectan UEs automáticamente.

Clonar copia credenciales internamente hacia un nuevo IMSI, pero no las muestra en la respuesta.

Eliminar requiere confirmación explícita. Una sesión UE activa puede persistir temporalmente hasta que sea desconectada o vuelva a registrarse.

## Modo Dry-Run

Con `LAIN5G_DRY_RUN=true`, las operaciones de escritura validan el payload pero devuelven:

```json
{
  "dry_run": true,
  "persisted": false
}
```

No insertan, modifican ni eliminan documentos reales.

## Pruebas

```bash
make subscribers-test
```

Las pruebas unitarias usan colecciones en memoria y no dependen de MongoDB real.

La integración real requiere confirmación explícita:

```bash
LAIN5G_ALLOW_INTEGRATION_WRITES=true make subscribers-integration-test
```

El flujo documentado valida conexión, listado, creación, edición, clonación, eliminación y posterior `make validate-5g-sa`.

## Riesgos

- El Compose base no monta `/var/run/docker.sock`; el override operativo opcional concede control equivalente a root del host.
- No expongas la aplicación fuera de loopback.
- No uses IMSI ni claves reales sin anonimizar.
- La existencia de un documento en MongoDB no demuestra autenticación exitosa del UE.
