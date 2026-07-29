# Lain5G-Lab

[![CI](https://github.com/guallycanazas/Lain5G/actions/workflows/ci.yml/badge.svg)](https://github.com/guallycanazas/Lain5G/actions/workflows/ci.yml)
[![Licencia: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Versión](https://img.shields.io/badge/version-1.0.0-blue.svg)](VERSION)

[README en inglés](README.md)

Lain5G-Lab es un entorno reproducible para desplegar, operar y validar redes de
laboratorio integradas 4G LTE/VoLTE y 5G SA/VoNR, además de un perfil 5G
non-standalone (NSA) experimental. Combina componentes consolidados de redes de
código abierto con aislamiento mediante Docker Compose, configuración
declarativa, un backend FastAPI, una interfaz React y registros trazables de
validación.

Lain5G-Lab no implementa desde cero un core móvil ni una RAN. Su contribución es
la integración, orquestación, validación y trazabilidad reproducibles de
Open5GS, UERANSIM, srsRAN, Kamailio, pyHSS, UHD y componentes relacionados. La
versión estable actual es la release solo de código fuente [`1.0.0`](VERSION).

> **Versión software probada y funcional.** Todos los flujos de red soportados
> completamente en software aprueban sus suites de validación: 4G LTE (14/14) y
> 5G SA (15/15). La verificación
> global `make softwarex-check` también aprueba 314 pruebas backend, 50 pruebas
> frontend, el build de producción, la verificación de código y Compose, los
> metadatos de publicación y los controles de archivos sensibles.

## Características principales

- Escenarios Docker Compose aislados para flujos software y SDR controlados.
- Redes de datos software 4G LTE y 5G SA validadas.
- Validación de registro LTE/5G, plano de usuario, túneles y conectividad.
- Perfiles declarativos con archivos locales ignorados para valores operativos.
- Herramientas FastAPI y React para observación local y operaciones protegidas.
- Validadores de escenarios y registros públicos anonimizados.
- Protecciones RF con autorización explícita, duración finita y parada de emergencia.

## Inicio rápido

Requisitos: GNU/Linux x86_64, Docker Engine, Docker Compose v2, Git, GNU Make,
`flock` de util-linux, soporte SCTP y `/dev/net/tun`.

```bash
git clone https://github.com/guallycanazas/Lain5G.git
cd Lain5G
./install.sh
```

En una máquina limpia, `install.sh` instala Python con soporte `venv`, Git,
Make, Docker, Compose y util-linux cuando faltan, habilita Docker, prepara la
configuración privada y descarga todos los componentes publicados. Use
`./install.sh --dry-run` para revisar el plan sin modificar el sistema.

Si el instalador lo solicita, ejecute `newgrp docker` antes de iniciar la
aplicación para activar el acceso al socket Docker en la terminal actual.

### Opción A: aplicación web

Inicie la interfaz operativa:

```bash
./lain5g app start --operations --open
```

Dentro de la app, el usuario elige 4G LTE o 5G SA software, o uno de los perfiles
RF 4G/5G protegidos. **Preparation** descarga
los componentes faltantes y **Scenarios** permite operar la red elegida. Las
simulaciones crean o conservan credenciales sintéticas privadas. La transmisión
RF exige preflight, perfil autorizado, checklist, frase exacta, duración limitada
y parada de emergencia. Detenga la interfaz con `./lain5g app stop` después de
finalizar cualquier sesión RF activa.

### Opción B: solo CLI

```bash
./lain5g
```

La consola interactiva ofrece 4G LTE ZMQ, 5G SA UERANSIM y los perfiles RF 4G/5G
protegidos. Descarga sus componentes y ejecuta las acciones disponibles. Al iniciar una
simulación, prepara automáticamente sus credenciales sintéticas privadas; los
perfiles RF conservan los mismos controles obligatorios de seguridad.

La app segura de solo observación se inicia con `./lain5g app start --open`.
Las credenciales se guardan en archivos locales ignorados, con permisos `0600`;
nunca se imprimen ni versionan. Consulte [Instalación](docs/installation.md),
[4G software](docs/4g_simulation.md) y [5G SA](docs/5g_sa.md).

## Redes software validadas

| Escenario | Propósito | Validación |
| --- | --- | --- |
| `4g-lte-sim` | EPC Open5GS + datos LTE con srsRAN ZMQ | **PASS (14/14)** |
| `5g-sa-sim` | 5GC Open5GS + datos 5G SA con UERANSIM | **PASS (15/15)** |

La evidencia histórica de señalización extremo a extremo permanece en
`results/public/`, pero esos escenarios completos no forman parte del catálogo público. Consulte
[Validación](docs/validation.md) y [Resultados públicos](results/public/README.md).

### Perfiles hardware protegidos

| Perfil | Propósito | Disponibilidad |
| --- | --- | --- |
| `4g-lte-x310` | 4G LTE e infraestructura IMS compacta siempre activa con eNB X300/X310 compatible | Flujo RF protegido con evidencia por ejecución |
| `5g-sa-x310` | 5G SA e infraestructura IMS compacta siempre activa con gNB X300/X310 compatible | Flujo RF protegido con evidencia por ejecución |

## Reproducibilidad y pruebas

```bash
make test
make verify
make softwarex-check
```

`make softwarex-check` es el comando único de verificación de release utilizado
por CI. Aprueba 314 pruebas backend con 78% de cobertura de líneas y 50 pruebas
frontend, seguido de TypeScript, build de producción, validación Compose y de
perfiles, metadatos, enlaces internos, resultados públicos y controles de
archivos sensibles.

## Arquitectura

- `backend/`: API FastAPI local de control y observación.
- `frontend/`: interfaz React de operación.
- `deployments/`: archivos Compose, configuraciones y scripts por escenario.
- `config/profiles/`: perfiles declarativos de escenarios y seguridad.
- `results/public/`: resúmenes de resultados revisados y anonimizados.
- `runs/`: registros locales ignorados que pueden contener información sensible.

Consulte [Arquitectura](docs/architecture.md) para ver el modelo completo de
componentes.

## Documentación

- [Instalación](docs/installation.md)
- [Configuración](docs/configuration.md)
- [Arquitectura](docs/architecture.md)
- [Validación](docs/validation.md)
- [Resultados públicos](results/public/README.md)
- [Reproducibilidad](docs/reproducibility/dependency-policy.md)
- [Matriz de versiones](docs/reproducibility/version-matrix.md)
- [Seguridad RF](docs/rf_safety.md)
- [Despliegue local seguro](docs/security/local-deployment.md)
- [Solución de problemas](docs/troubleshooting.md)

Los registros detallados de auditoría, seguridad, aspectos legales y evidencia
permanecen en `audit/`, `docs/security/`, `docs/legal/` y `results/public/`, no
en esta presentación general.

## Limitaciones

- Lain5G-Lab es un entorno de investigación y educación, no una red de
  producción, una implementación de referencia 3GPP ni una plataforma de
  conformidad.
- Los resultados de simulación software no deben extrapolarse a SDR ni a UE
  comerciales.
- El comportamiento de UE comerciales y los resultados RF requieren experimentos
  autorizados independientes.
- Los artefactos públicos son resúmenes anonimizados, no trazas de protocolo.

## Autores

- **Willian Roy Canazas Rosas**
- **Manuel Ismael Prieto Tito**

Afiliación: **Universidad Nacional de San Agustín de Arequipa**.

## Citación

Los metadatos de citación están disponibles en [CITATION.cff](CITATION.cff). El
DOI del software y la cita del artículo SoftwareX se añadirán únicamente después
de una publicación archivada. Actualmente no se afirma un DOI ni un artículo
SoftwareX publicado.

## Licencia

El código propio está disponible bajo la [licencia MIT](LICENSE). Los componentes
upstream integrados conservan sus propias licencias y condiciones de
redistribución; consulte [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Soporte y seguridad

Use GitHub Issues para errores reproducibles y no sensibles. No publique
secretos, identificadores de suscriptores, planes RF, tokens ni logs privados.
Consulte [SUPPORT.md](SUPPORT.md) para soporte y orientación sobre reportes
sensibles.
