# Lain5G-Lab

[![CI](https://github.com/guallycanazas/Lain5G/actions/workflows/ci.yml/badge.svg)](https://github.com/guallycanazas/Lain5G/actions/workflows/ci.yml)
[![Licencia: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Versión](https://img.shields.io/badge/version-1.0.0--rc.1-blue.svg)](VERSION)

[README en inglés](README.md)

Lain5G-Lab es un entorno reproducible para desplegar, operar y validar escenarios
experimentales 4G LTE/EPC/IMS, 5G standalone (SA) y 5G non-standalone (NSA)
experimental. Combina componentes consolidados de redes de código abierto con
aislamiento mediante Docker Compose, configuración declarativa, un backend
FastAPI, una interfaz React y registros trazables de validación.

Lain5G-Lab no implementa desde cero un core móvil ni una RAN. Su contribución es
la integración, orquestación, validación y trazabilidad reproducibles de
Open5GS, UERANSIM, srsRAN, Kamailio, pyHSS, UHD y componentes relacionados. La
versión actual es el candidato solo de código fuente [`1.0.0-rc.1`](VERSION).

## Características principales

- Escenarios Docker Compose aislados para flujos software y SDR controlados.
- Ejemplos 4G LTE, registro IMS 4G y 5G SA completamente software.
- Perfiles declarativos con archivos locales ignorados para valores operativos.
- Herramientas FastAPI y React para observación local y operaciones protegidas.
- Validadores de escenarios y registros públicos anonimizados.
- Protecciones RF con autorización explícita, duración finita y parada de emergencia.

## Inicio rápido

Requisitos: GNU/Linux x86_64, Docker Engine, Docker Compose v2, Git, GNU Make,
soporte SCTP y `/dev/net/tun`.

Este ejemplo ejecuta Open5GS y UERANSIM completamente en software y no usa RF:

```bash
git clone https://github.com/guallycanazas/Lain5G.git
cd Lain5G

cp deployments/5g-sa/.env.example deployments/5g-sa/.env
# Add laboratory-only subscriber values to the ignored local .env file.

./lain5g images pull 5g-sa
make start-5g-sa
make validate-5g-sa
make stop-5g-sa
```

Use solo valores de suscriptor sintéticos o de laboratorio. Consulte
[Instalación](docs/installation.md) y [5G SA](docs/5g_sa.md) para más detalles.

## Escenarios

| Escenario | Propósito | Estado actual |
| --- | --- | --- |
| `5g-sa-sim` | 5G SA software con Open5GS + UERANSIM | Validado en simulación |
| `4g-lte-sim` | Datos LTE con Open5GS + srsRAN ZMQ | Validado en simulación |
| `4g-ims-sim` | LTE software + registro IMS de laboratorio | Validado en simulación |
| `5g-vonr-sim` | 5G SA software + IMS de laboratorio | No validado |
| `4g-lte-x310` | LTE con hardware X300/X310 compatible | Parcialmente validado |
| `5g-sa-x310` | 5G SA con hardware X300/X310 compatible | No validado |
| `5g-nsa-x310` | LTE + NR EN-DC experimental | Parcialmente validado |
| `ims-real` | Paquete separado Open5GS, pyHSS y Kamailio | Parcial / dependiente de dry-run |

El estado se aplica únicamente al alcance indicado. `5g-sa-sim` utiliza el
despliegue `5g-sa` y el resultado público `4g-ims-sim` utiliza el perfil
operativo `4g-volte-sim`. Consulte [Validación](docs/validation.md) y
[Resultados públicos](results/public/README.md) para conocer la evidencia y sus
límites exactos.

## Pruebas

```bash
make test
make verify
make softwarex-check
```

El candidato actual aprueba 262 pruebas backend con 77% de cobertura de líneas
backend y 42 pruebas frontend. También aprueba localmente la comprobación
TypeScript, el build de producción frontend, la validación Compose y de perfiles,
los metadatos y los controles de archivos sensibles. Estas comprobaciones
software no validan RF ni la operación con UE comerciales.

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
- No se han demostrado una llamada VoLTE completa ni RTP bidireccional.
- No se han validado VoNR, registro y datos 5G SA con UE comercial ni un plano de
  usuario NR estable.
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
