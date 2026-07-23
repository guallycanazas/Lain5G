# Versiones y trazabilidad

La versión autoritativa de Lain5G-Lab está en `VERSION`. El candidato actual es
`1.0.0-rc.1`. La API, el frontend, las etiquetas OCI, las imágenes derivadas y
el changelog se comprueban contra esa fuente con:

```bash
make version-check
```

La matriz completa, las fuentes de evidencia, las plataformas de cada manifest
y los riesgos no resueltos están en
`docs/reproducibility/version-matrix.md`. La política de actualización está en
`docs/reproducibility/dependency-policy.md`.

## Componentes software

| Componente | Ref legible | Commit inmutable |
| --- | --- | --- |
| Open5GS | `v2.7.5` | `7dfd9a39649700c24c22f1978ed7a35541a72cca` |
| UERANSIM | `v3.2.6` | `384636f4fcf46b8c86109790ff3e2cd242b53556` |
| srsRAN 4G | `release_23_11` | `eea87b1d893ae58e0b08bc381730c502024ae71f` |
| srsRAN Project | `release_24_10_1` | `ef4b0749a12a3b1a8347ae01c937a621603b4069` |
| UHD | `v4.10.0.0` | `2af4ddb96219a99d2300804830e0971f79557b23` |
| Kamailio | `5.8.8` | `053181eb9c3136836cb272584b582484a9a11b48` |

Los tags se conservaron para lectura humana, pero cada Dockerfile descarga,
selecciona y verifica el commit completo. CoreDNS `1.11.3`, MongoDB y MariaDB,
así como todas las bases de Dockerfile, se fijan por digest de manifest.

Las imágenes publicadas del catálogo `gually/lain5g-*` están fijadas por digest
y actualmente solo ofrecen Linux/amd64. Los digests de índice multi-plataforma
se conservaron para las bases oficiales cuando el registro los ofrecía; esto no
constituye una afirmación de que el software propio haya sido probado en todas
esas arquitecturas.

## Dependencias de aplicación

- Python: requisitos directos exactos en `backend/requirements*.txt` y cierre
  runtime/desarrollo exacto en `backend/constraints.txt`.
- Frontend: cierre e integridades en `frontend/package-lock.json`; instalar con
  `npm ci` mediante `make frontend-install`.
- IMS real: bases y etiquetas derivadas en
  `deployments/ims-real/images.lock.yaml`.

## Límites de reproducción

Los repositorios APT usados durante los builds no son snapshots. Por ello, los
paquetes de sistema pueden cambiar aunque la base y el código fuente estén
fijados. RTPengine usa el canal verificado `26.0` y valida el checksum del
keyring, pero ese canal aún puede recibir revisiones distintas por arquitectura.

La imagen local `lain5g-lab/open5gs:local` contiene los binarios EPC
`open5gs-mmed`, `open5gs-hssd`, `open5gs-sgwcd`, `open5gs-sgwud`,
`open5gs-pcrfd`, `open5gs-smfd` y `open5gs-upfd`. Open5GS `v2.7.5` no instala
`open5gs-pgwcd` ni `open5gs-pgwud`; los servicios 4G `pgwc` y `pgwu` ejecutan
`open5gs-smfd` y `open5gs-upfd`.

Antes de publicar resultados, archive el commit de Lain5G-Lab, la salida de
`make version-check`, los argumentos de construcción y `docker image inspect`
de cada imagen final. Un tag `:local` no sustituye el digest de la imagen ni un
artefacto archivado con DOI.
