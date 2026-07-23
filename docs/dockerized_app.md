# Aplicación Dockerizada

El stack de aplicación dockerizado ejecuta dos servicios separados del laboratorio 5G SA:

- `frontend`: Nginx sirviendo la aplicación React y proxy `/api`.
- `backend`: FastAPI; el acceso al Docker del host es un opt-in separado.

No reemplaza ni modifica `deployments/5g-sa/docker-compose.yml`.

## Preparación

```bash
cp .env.app.example .env.app
```

Edita `.env.app` y define `LAIN5G_PROJECT_ROOT` con la ruta absoluta del repositorio en el host:

```env
LAIN5G_PROJECT_ROOT=/path/to/Lain5G
```

La ruta debe ser absoluta. En el modo operativo opcional también debe coincidir con la ruta que ve el daemon Docker del host porque los despliegues contienen bind mounts relativos.

Si quieres que el backend ejecute comandos reales, prepara también el entorno del escenario y sigue el opt-in de `docs/security/local-deployment.md`:

```bash
cp deployments/5g-sa/.env.example deployments/5g-sa/.env
```

## Uso

```bash
make app-up
make app-ps
make app-logs
make app-down
```

Interfaz web:

```text
http://127.0.0.1:8080
```

API expuesta para depuración local:

```text
http://127.0.0.1:8000/api/health
```

## Build Manual

```bash
make app-build
```

El build del backend usa el contexto raíz para copiar `VERSION`; sus paquetes
Python se resuelven con `backend/constraints.txt`. El frontend instala desde el
lockfile mediante `npm ci`.

Equivalente:

```bash
docker compose --env-file .env.app -f docker-compose.app.yml build
```

## Modo Dry-Run

Para probar la aplicación sin iniciar contenedores 5G SA reales:

```env
LAIN5G_DRY_RUN=true
```

En este modo el backend devuelve los comandos que habría ejecutado y las validaciones aparecen como `NOT_TESTED`.

## Seguridad Operativa

- El Compose base no monta `/var/run/docker.sock`, usa el proyecto en solo lectura y publica solo en loopback.
- `docker-compose.app-operations.yml` habilita explícitamente un proyecto escribible y el socket Docker, que equivale a control root del host.
- Las mutaciones requieren además `LAIN5G_MUTATING_OPERATIONS_ENABLED=true`.
- No expongas la aplicación fuera de la máquina local.
- `.env.app`, `backend/.env`, `frontend/.env` y `deployments/5g-sa/.env` no deben versionarse.
- No uses claves reales ni IMSI reales sin anonimizar en el laboratorio.
- Ver `docs/security/local-deployment.md` para el comando exacto de opt-in.

## Relación con el Laboratorio 5G SA

El backend llama a los scripts existentes:

```text
deployments/5g-sa/scripts/start.sh
deployments/5g-sa/scripts/stop.sh
deployments/5g-sa/scripts/restart.sh
deployments/5g-sa/scripts/status.sh
deployments/5g-sa/scripts/logs.sh
deployments/5g-sa/scripts/validate.sh
```

El stack de aplicación vive en `docker-compose.app.yml`. El stack operativo 5G SA sigue viviendo en `deployments/5g-sa/docker-compose.yml`.

## Gestión de Suscriptores

El backend usa `pymongo` para acceder al MongoDB de Open5GS cuando el laboratorio está activo. La app no depende de MongoDB para arrancar: si 5G SA está detenido, `/api/subscribers/connection` devuelve `disconnected` o `timeout` y el resto de la aplicación sigue funcionando.

La conexión se controla con:

```env
LAIN5G_OPEN5GS_MONGO_URI=mongodb://mongo:27017/open5gs
LAIN5G_OPEN5GS_MONGO_DATABASE=open5gs
LAIN5G_OPEN5GS_SUBSCRIBER_COLLECTION=subscribers
LAIN5G_OPEN5GS_DOCKER_NETWORK=lain5g-lab-5g-sa-core
```

El backend solo intenta unirse a la red Docker 5G SA cuando el contenedor MongoDB está en ejecución y `LAIN5G_MUTATING_OPERATIONS_ENABLED=true`. El modo base nunca modifica redes Docker.

Ver `docs/subscribers.md`.
