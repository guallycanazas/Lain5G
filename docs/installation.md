# Installation

## Requisitos

- Docker con soporte de Compose v2.
- Kernel con SCTP y `/dev/net/tun` disponible.
- Acceso a Internet para clonar y compilar Open5GS y UERANSIM durante `make build-5g-sa`.
- Para X310: red host preparada para USRP y herramientas UHD en host si se desea validar hardware fuera del contenedor.

## Preparación recomendada

Comprueba primero que la versión y los locks no se contradicen:

```bash
make version-check
```

La consola comprueba Docker, Compose, TUN, espacio, configuración e imágenes:

```bash
./lain5g
```

Selecciona `Imágenes y componentes` para comprobar o descargar lo necesario. Las imágenes compatibles se descargan desde Docker Hub y se etiquetan automáticamente con los nombres internos del laboratorio; no se compila ni se inicia ningún servicio.

La misma preparación está disponible en la interfaz web después de `make app-up`:

```text
http://localhost:8080/preparation
```

También se puede preparar un perfil directamente:

```bash
./lain5g doctor 4g-lte-sim
./lain5g images pull 4g-lte-sim
```

Para descargar todos los componentes publicados:

```bash
make images-pull
```

## Construcción alternativa

La construcción local solo es necesaria para desarrollar o modificar los componentes:

```bash
make build-5g-sa
```

Para 4G software:

```bash
make build-4g-lte-sim
make build-4g-volte-sim
```

Para 4G X310:

```bash
make build-4g-lte-x310
```

La imagen X310 compila UHD y puede tardar bastante más que la ruta software.

La API Dockerizada se construye desde el contexto raíz para incluir el archivo
autoritativo `VERSION`; use `docker build -f backend/Dockerfile .` si necesita
construirla fuera de Compose.

Esto crea las mismas etiquetas locales que la descarga automática:

- `lain5g-lab/open5gs:local`
- `lain5g-lab/ueransim:local`
- `lain5g-lab/srsran4g-sim:local`
- `lain5g-lab/srsran4g-uhd:local`
- `lain5g-lab/kamailio:local`
- `lain5g-lab/ims-dns:local`

Las imágenes se construyen desde repositorios oficiales, no desde imágenes de terceros.

## Configuración inicial

```bash
cp deployments/5g-sa/.env.example deployments/5g-sa/.env
nano deployments/5g-sa/.env
```

Define `SUBSCRIBER_KEY` y `SUBSCRIBER_OPC` con valores de laboratorio de 32 caracteres hexadecimales. No uses claves reales.

Para 4G:

```bash
cp deployments/4g-volte/common/.env.example deployments/4g-volte/common/.env
nano deployments/4g-volte/common/.env
```

Los archivos RF reales `channel-plan.yaml` y `safety-manifest.yaml` no se versionan; ver `docs/rf_safety.md`.
