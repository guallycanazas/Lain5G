# Lain5G-Lab

[Read in English](README.md)

Lain5G-Lab es un entorno de investigación reproducible para integrar, operar y
evaluar escenarios de laboratorio 4G LTE/EPC/IMS, 5G standalone (SA) y 5G
non-standalone (NSA) experimental. Combina proyectos upstream consolidados con
aislamiento de escenarios, configuración declarativa, protecciones operativas,
registros de validación y una interfaz FastAPI/React.

## Estado de la versión

La versión definida en [VERSION](VERSION) es **`1.0.0-rc.1`**.
[CHANGELOG.md](CHANGELOG.md) todavía la identifica como no publicada. Es un
candidato de versión, no una versión final, una red móvil de producción, una
implementación de referencia 3GPP, un resultado de conformidad ni una
publicación en SoftwareX.

Los artefactos públicos permiten sostener resúmenes acotados de validadores
software, no trazas de protocolo revisables de forma independiente. Las
observaciones con hardware y UE comercial siguen siendo no públicas y parciales,
y varios resultados de radio y voz no están validados. Para evitar
divergencias, la única clasificación normativa es la
[tabla canónica de capacidades en inglés](README.md#canonical-capability-status).
Esta traducción explica su contexto, pero no mantiene una segunda matriz.

Este es un **candidato solo de código fuente**. La revisión legal y del SBOM no
autoriza publicar ni volver a publicar imágenes de contenedor del proyecto.

## Problema científico y contribución

Reproducir un experimento de red celular requiere mucho más que iniciar un core.
Los parámetros de core, RAN, IMS, suscriptores, redes de contenedores, host y
radio deben ser coherentes; las revisiones de software y el entorno deben quedar
registrados; y la disponibilidad operativa no debe confundirse con un resultado
científico extremo a extremo.

Lain5G-Lab aborda ese problema de integración mediante:

- escenarios Docker Compose aislados para rutas software y rutas SDR
  controladas;
- perfiles versionados y archivos locales ignorados para valores sensibles o
  específicos del laboratorio;
- flujos compartidos entre terminal, FastAPI y React;
- validadores y registros de ejecución con resultados y procedencia explícitos;
- una frontera de resultados públicos anonimizados; y
- controles RF de autorización explícita, duración finita, auto-stop, logs y
  parada de emergencia.

La contribución propia es la orquestación, integración, configuración,
validación y trazabilidad. Open5GS, UERANSIM, srsRAN, UHD, Kamailio, pyHSS,
RTPengine, CoreDNS, MongoDB y MariaDB aportan las funciones upstream de core,
RAN, IMS, medios, DNS y bases de datos. Lain5G-Lab no certifica esos proyectos,
no implementa desde cero un core o una RAN y no certifica conformidad 3GPP.

## Estado y procedencia de la evidencia

Las clasificaciones `VALIDATED`, `PARTIALLY_VALIDATED`, `NOT_VALIDATED`,
`SIMULATION_ONLY` y `DRY_RUN_ONLY` se definen y aplican exclusivamente en la
[tabla canónica](README.md#canonical-capability-status). Un contenedor saludable,
un preflight aprobado, un único marcador de señalización o un proceso que
termina correctamente no constituyen por sí solos una validación extremo a
extremo.

La procedencia debe interpretarse de la siguiente forma:

- **Commit fuente:** los cuatro intentos públicos nuevos registran
  `12c4a38404bbaf240c698a056e3f47182081ab5c` como el código exacto evaluado.
- **Commit inicial de publicación de artefactos:**
  `060e669d3f65e1844a702b1b5264be6933ef45c2`, hijo directo del anterior, añade
  los JSON y resúmenes anonimizados. Publicar los artefactos en ese commit no
  significa que el escenario se ejecutara de nuevo. El candidato actual corrige
  el resultado del criterio de finalización VoNR y el hash de su resumen sin una
  nueva ejecución.
- **Evidencia pública:** [results/public](results/public/) contiene resúmenes de
  validadores
  versionados y conformes con el esquema, sin logs crudos, capturas, claves,
  identificadores reales, direcciones privadas, números de serie ni detalles RF
  operativos. Al excluir ese material, los resúmenes no permiten reconstruir de
  manera independiente los eventos de protocolo.
- **Evidencia privada:** `runs/` y los logs operativos mutables pueden contener
  información sensible y no son reproducibles públicamente.
- **Evidencia histórica:** las ejecuciones y auditorías de commits anteriores,
  no relacionados o desconocidos sirven como contexto, pero no como evidencia
  del candidato actual. La [auditoría del 22 de julio](audit/scenario-status.md)
  y su línea base de 149 pruebas backend son una instantánea histórica.

Los resultados públicos nuevos son exactos y de alcance limitado:

- [5G SA software, `run-20260723-054913`](results/public/5g-sa-sim/run-20260723-054913.json):
  15/15 comprobaciones `PASS`, `SIMULATION_ONLY`.
- [LTE software, `run-20260723-055025`](results/public/4g-lte-sim/run-20260723-055025.json):
  14/14 comprobaciones `PASS`, `SIMULATION_ONLY`.
- [IMS 4G de laboratorio, `run-20260723-055149`](results/public/4g-ims-sim/run-20260723-055149.json):
  22/22 comprobaciones `PASS`, `SIMULATION_ONLY`; reporta comprobaciones de
  registro SIP Digest de laboratorio, no AKA, Cx, Rx, llamada ni medios
  bidireccionales.
- [VoNR software, `run-20260723-055328`](results/public/5g-vonr-sim/run-20260723-055328.json):
  ejecución `BLOCKED` por timeout, `NOT_VALIDATED`, sin criterios de escenario
  evaluados. El validador alcanzó su límite de seis minutos y el artefacto mide
  413 segundos para el intento completo.

Las comprobaciones locales no RF reportan **262 pruebas backend aprobadas, 77%
de cobertura de líneas backend, 42 pruebas frontend aprobadas y un build de
producción frontend correcto**. No hay cobertura frontend configurada ni se
afirma una ejecución alojada de CI.

## Observaciones privadas del laboratorio

Una sesión no pública con hardware X-Series observó dos cadenas RF mediante
UHD. Ese dato solo identifica la clase de montaje observado y no convierte la
sesión en evidencia pública, ligada a commit o reproducible para la versión.

- Los logs LTE comerciales contienen marcadores compatibles con S1, RRC,
  contexto/bearer y UE conectado. Falta un resultado persistido y correlacionado
  del bearer de datos, por lo que no se afirma attach completo con datos activos.
- Las observaciones IMS 4G contienen marcadores compatibles con bearers
  `internet` e `ims`, Rx, AKA/Cx, registro autenticado, `SUBSCRIBE`, `NOTIFY` e
  `INVITE`. No se encontró ni se afirma `MESSAGE`. Falta un artefacto único,
  anónimo y ligado a commit.
- Las observaciones NSA incluyen dos cadenas RF activas, S1 aceptado,
  marcadores de attach LTE, capacidad EN-DC indicada por el UE, reconfiguración
  RRC completada y estado de usuario conectado. También incluyen advertencias
  RLC en DRB1 y eventos RLF. No demuestran un plano de usuario NR estable ni
  rendimiento.

La tabla canónica mantiene `PARTIALLY_VALIDATED` para las observaciones privadas
de LTE comercial, IMS real 4G y NSA. Mantiene `NOT_VALIDATED` para la llamada
VoLTE completa, 5G SA con UE comercial, el plano de usuario NR estable y VoNR
sobre RF. El modo 5G de `ims-real` permanece `DRY_RUN_ONLY`. Para VoLTE faltan,
en una misma ejecución correlacionada, una respuesta final exitosa al `INVITE`,
`ACK`, `BYE` y RTP bidireccional.

## Arquitectura y escenarios

El repositorio separa control, escenarios y evidencia:

- `backend/` contiene la API local FastAPI y `frontend/` la interfaz React.
- `config/profiles/` define configuración y estado de seguridad por perfil.
- `deployments/` contiene Compose, configuración y scripts operativos por
  escenario.
- Los proyectos, redes y volúmenes Compose aíslan los escenarios.
- `runs/` conserva resultados operativos locales ignorados por Git.
- `results/public/` acepta únicamente resúmenes revisados y anonimizados.

Open5GS proporciona EPC/5GC; UERANSIM, el gNB y UE software; srsRAN 4G, las
rutas LTE ZMQ y SDR; srsRAN Project, el gNB SDR 5G; UHD, el acceso USRP; y
Kamailio, pyHSS, CoreDNS, RTPengine y las bases seleccionadas, los paquetes IMS.
Consulte [la arquitectura](docs/architecture.md) y
[los avisos de terceros](THIRD_PARTY_NOTICES.md).

Los escenarios principales son:

- `5g-sa` / `5g-sa-sim`: Open5GS y UERANSIM para 5G SA software.
- `4g-lte-sim`: EPC Open5GS y srsRAN 4G por ZMQ, sin IMS.
- `4g-volte-sim`: LTE software e IMS compacto de laboratorio; el artefacto
  público se denomina `4g-ims-sim` para reflejar el alcance medido.
- `5g-vonr-sim`: 5G SA e IMS de laboratorio empaquetados; el intento público
  actual está bloqueado y no validado.
- `4g-lte-x310`: ruta LTE SDR bloqueada para RF por defecto; el nombre histórico
  se conserva aunque los perfiles compatibles también aceptan X300.
- `5g-sa-x310`: preparación SDR y ruta gNB 5G SA controlada.
- `5g-nsa-x310`: prototipo EN-DC LTE B7 más NR n3.
- `ims-real`: core/IMS 4G o 5G separado, sin RAN ni UE suministrados.

No se extrapolan resultados entre simulación, SDR y UE comercial.

## Requisitos

Los escenarios software requieren un host GNU/Linux x86_64, Docker Engine,
Docker Compose v2, Git, GNU Make, soporte SCTP, `/dev/net/tun`, espacio suficiente
y acceso a Internet para la primera descarga o construcción. Python y Node.js/npm
solo son necesarios al ejecutar backend, frontend o comprobaciones de desarrollo
fuera de contenedores.

Las revisiones exactas se documentan en la
[matriz de versiones](docs/reproducibility/version-matrix.md). No se afirma el
mismo comportamiento en arquitecturas no evaluadas o con dependencias
sustituidas.

Los escenarios SDR requieren además un equipo X300/X310 autorizado, FPGA y
firmware compatibles, daughterboards adecuados, Ethernet dedicado, permisos y
planificación apropiados para UHD, y un entorno conducido, blindado o formalmente
autorizado. Antes de transmitir se requieren manifiesto local de seguridad, plan
de canal, duración finita, atenuación y autorización del operador.

## Inicio seguro

### Aplicación de observación por defecto

La aplicación base es solo de observación por defecto. Publica únicamente en
loopback, monta el repositorio en solo lectura, no monta el socket Docker y
mantiene deshabilitadas las mutaciones, las descargas de imágenes y el control RF
web.

```bash
cp .env.app.example .env.app
# Define LAIN5G_PROJECT_ROOT con la ruta absoluta del repositorio.
# Conserva LAIN5G_MUTATING_OPERATIONS_ENABLED=false.
make app-up
```

Abra `http://127.0.0.1:8080`. Para el comportamiento no operativo más estricto,
defina también `LAIN5G_DRY_RUN=true`. Detenga la aplicación base con
`make app-down`.

El control operativo de Docker requiere dos opt-in independientes en una
estación dedicada y de confianza: definir
`LAIN5G_MUTATING_OPERATIONS_ENABLED=true` en `.env.app` y aplicar explícitamente
el override operativo:

```bash
docker compose --env-file .env.app \
  -f docker-compose.app.yml \
  -f docker-compose.app-operations.yml \
  up -d --build
```

El override vuelve escribible el montaje del proyecto y añade
`/var/run/docker.sock`, equivalente a control root del host. El override solo no
habilita las rutas mutables; el flag solo tampoco concede acceso a Docker o
escritura. Ninguno autoriza RF. Use los mismos dos archivos con `down` para
retirar el stack y consulte el [despliegue local seguro](docs/security/local-deployment.md).

### Ejemplo software mínimo

Este ejemplo crea recursos Docker, pero no utiliza SDR ni RF. Los valores de
suscriptor deben ser exclusivamente de laboratorio y permanecer en el `.env`
local ignorado.

```bash
cp deployments/5g-sa/.env.example deployments/5g-sa/.env
# Define localmente SUBSCRIBER_KEY y SUBSCRIBER_OPC de laboratorio.
./lain5g images pull 5g-sa
make start-5g-sa
make validate-5g-sa
make stop-5g-sa
```

No use claves, IMSI/MSISDN, direcciones privadas ni planes RF de una red real.
Consulte [5G SA](docs/5g_sa.md) e
[instalación](docs/installation.md).

## Validación y reproducibilidad

Los validadores reportan `PASS`, `FAIL`, `WARNING` o `NOT_TESTED` por
comprobación y escriben registros locales en `runs/<run-id>/`. Una afirmación de
versión requiere además commit fuente exacto, alcance del comando, entorno,
configuración no sensible, criterios de éxito, estado terminal y evidencia
correlacionada. Los resúmenes públicos deben cumplir el esquema y los controles
de contenido sensible de [results/public](results/public/).

El registro IMS no basta para afirmar voz extremo a extremo. Se debe
correlacionar el `INVITE` originador con respuesta final exitosa, `ACK`,
terminación mediante `BYE` y RTP bidireccional. Ninguna evidencia actual cumple
todos estos requisitos.

Las comprobaciones software no RF se pueden repetir con:

```bash
make backend-cov
make frontend-test
make frontend-build
```

Las 262 pruebas backend, 42 frontend, el 77% de cobertura de líneas backend y el
build aprobado no establecen cobertura frontend ni validan RF o capacidades
celulares.

Para comparar un experimento:

1. Registre revisión Git y versión exactas.
2. Use las versiones y digests fijados en la documentación reproducible.
3. Registre SO, CPU, memoria, Docker/Compose, NIC/MTU y, cuando corresponda,
   información no sensible de SDR, FPGA y daughterboards.
4. Conserve comando, estado terminal, configuración anonimizada, JSON de
   validación y logs correlacionados bajo un único identificador de ejecución.
5. Publique solo resúmenes revisados; no publique `runs/` directamente.

La política de dependencias está en
[docs/reproducibility/dependency-policy.md](docs/reproducibility/dependency-policy.md).

## Reportado y no demostrado

Dentro del alcance público, el candidato publica tres resúmenes de validadores
software: 5G SA, LTE e IMS 4G de laboratorio. Son informes anonimizados y
conformes con el esquema, no evidencia de protocolo revisable de forma
independiente. El intento VoNR software se publica como bloqueado, no como
resultado positivo.

Las observaciones privadas LTE, IMS real y NSA son contexto experimental
parcial, no demostraciones públicas. No se han demostrado, en su alcance
declarado, una llamada VoLTE completa, registro y datos 5G SA con UE comercial,
un plano de usuario NR estable, ejecución 5G de `ims-real` ni VoNR sobre RF.
Tampoco se afirman latencia, throughput, pérdida, estabilidad RF,
reproducibilidad multihost ni conformidad 3GPP.

## Seguridad RF

Las rutas RF están deshabilitadas por defecto y se excluyen deliberadamente del
inicio rápido. No transmita en espectro licenciado sin autorización legal,
técnica e institucional. Prefiera entornos conducidos o blindados con atenuación
adecuada, duración finita, auto-stop y parada de emergencia. El proyecto no
actualiza automáticamente firmware o FPGA.

El acceso mutable de la aplicación y el socket Docker no son autorización RF.
Siga [docs/rf_safety.md](docs/rf_safety.md) y el checklist específico antes de
cualquier trabajo con hardware.

## Documentación

- [Instalación](docs/installation.md),
  [configuración](docs/configuration.md) y
  [troubleshooting](docs/troubleshooting.md)
- [Arquitectura](docs/architecture.md) y
  [validación](docs/validation.md)
- [4G LTE/IMS](docs/4g_volte.md),
  [IMS real](docs/real_ims.md) y
  [criterios VoLTE](docs/volte_validation.md)
- [5G SA](docs/5g_sa.md), [5G VoNR](docs/5g_vonr.md) y
  [checklist para UE comercial](docs/5g_x310_cots_ue_checklist.md)
- [Despliegue local seguro](docs/security/local-deployment.md),
  [modelo de amenazas](docs/security/threat-model.md) y
  [seguridad RF](docs/rf_safety.md)
- [Matriz de versiones](docs/reproducibility/version-matrix.md) y
  [dependencias de terceros](docs/third_party.md)

## Citación y futuro artículo SoftwareX

[CITATION.cff](CITATION.cff) contiene solo metadatos software del candidato y no
anuncia una cita preferida de artículo. No se afirma envío, aceptación,
publicación ni DOI. La etiqueta colectiva de contribuidores no es
una lista final de autores científicos; nombres, afiliaciones, ORCID, orden y
contacto correspondiente requieren confirmación directa según
[AUTHORS.md](AUTHORS.md).

Si en el futuro se emite un DOI archivado o se publica un artículo, los
metadatos deberán actualizarse a partir del registro emitido, sin inventar
información.

## Licencia, terceros y soporte

El código propio se distribuye bajo [licencia MIT](LICENSE). Esa licencia no
relicencia el software upstream, las imágenes ni la configuración importada.
Cada componente conserva sus condiciones; revise
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) y las limitaciones documentadas
del SBOM antes de redistribuir. Este candidato solo de código fuente no autoriza
publicar binarios ni imágenes de contenedor.

El soporte de `1.0.0-rc.1` es comunitario y de mejor esfuerzo, sin SLA ni soporte
operativo RF. Siga [SUPPORT.md](SUPPORT.md), comparta solo información
reproducible y anonimizada, y use [SECURITY.md](SECURITY.md) para asuntos de
seguridad. No se afirma un correo de soporte ni una mesa institucional.
El canal privado para vulnerabilidades sigue siendo un bloqueo de la versión
final.
