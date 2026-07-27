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
> completamente en software aprueban sus suites de validación: 4G LTE (14/14),
> 4G VoLTE/IMS (22/22), 5G SA (15/15) y 5G VoNR/IMS (25/25). La verificación
> global `make softwarex-check` también aprueba 280 pruebas backend, 48 pruebas
> frontend, el build de producción, la verificación de código y Compose, los
> metadatos de publicación y los controles de archivos sensibles.

## Características principales

- Escenarios Docker Compose aislados para flujos software y SDR controlados.
- Redes software 4G LTE/VoLTE y 5G SA/VoNR validadas.
- Validación de registro LTE/5G, plano de usuario, IMS, DNS y SIP autenticado.
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
# Añada valores de suscriptor exclusivos del laboratorio al archivo .env ignorado.

./lain5g images pull 5g-sa
./lain5g scenario start 5g-sa
./lain5g scenario validate 5g-sa
./lain5g scenario stop 5g-sa
```

Ejecute `./lain5g` sin argumentos para usar la consola interactiva, que permite
revisar el equipo, descargar imágenes, configurar
perfiles, iniciar/validar/detener escenarios y administrar la aplicación web.
También puede abrir directamente la app operativa, con descargas y control de
escenarios software habilitados pero RF desactivada:

```bash
./lain5g app start --operations --open
```

Para configurar el perfil mediante el asistente use
`./lain5g profile wizard 5g-sa`. La app segura de solo observación se inicia con
`./lain5g app start --open`.

Use solo valores de suscriptor sintéticos o de laboratorio. Consulte
[Instalación](docs/installation.md) y [5G SA](docs/5g_sa.md) para más detalles.

## Redes software validadas

| Escenario | Propósito | Validación |
| --- | --- | --- |
| `4g-lte-sim` | EPC Open5GS + datos LTE con srsRAN ZMQ | **PASS (14/14)** |
| `4g-volte-sim` | 4G LTE + EPC + señalización IMS/VoLTE | **PASS (22/22)** |
| `5g-sa-sim` | 5GC Open5GS + datos 5G SA con UERANSIM | **PASS (15/15)** |
| `5g-vonr-sim` | 5G SA + dos sesiones PDU + señalización IMS/VoNR | **PASS (25/25)** |

El resultado público `4g-ims-sim` corresponde al perfil operativo
`4g-volte-sim` y valida LTE, EPC, IMS y registro SIP autenticado. La validación
operacional más reciente de `5g-vonr-sim` cubre el 5GC, NG Setup, registro UE,
sesiones PDU de internet e IMS, ambos túneles UE, conectividad de datos, DNS IMS,
acceso al P-CSCF y registro SIP autenticado. Consulte
[Validación](docs/validation.md) y [Resultados públicos](results/public/README.md)
para conocer el modelo de evidencia.

### Perfiles hardware y experimentales protegidos

| Perfil | Propósito | Disponibilidad |
| --- | --- | --- |
| `4g-lte-x310` | EPC/IMS 4G con eNB X300/X310 compatible | Core e IMS funcionales; RF requiere hardware autorizado |
| `5g-sa-x310` | 5G SA con gNB X300/X310 compatible | Flujo RF protegido disponible; depende del hardware |
| `5g-nsa-x310` | LTE + NR EN-DC experimental | Perfil experimental protegido disponible |
| `ims-real` | Runtime separado Open5GS, pyHSS y Kamailio | Paquete operacional; depende del entorno |

## Reproducibilidad y pruebas

```bash
make test
make verify
make softwarex-check
```

`make softwarex-check` es el comando único de verificación de release utilizado
por CI. Aprueba 280 pruebas backend con 77% de cobertura de líneas y 48 pruebas
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
- El alcance VoLTE y VoNR validado cubre registro de red, sesiones de datos,
  acceso IMS y señalización SIP autenticada. La calidad de audio, el rendimiento
  RTP, el comportamiento de UE comerciales y los resultados RF son experimentos
  separados.
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
