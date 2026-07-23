# Configuration

## Fuentes editables

- `config/profiles/*.yaml` contiene perfiles versionados. Los identificadores de
  simulación son vectores sintéticos; los perfiles RF no constituyen una
  autorización operativa.
- Los `.env` de escenario son locales e ignorados por Git.
- Los archivos bajo `deployments/*` son salidas efectivas o plantillas que deben
  revisarse después de aplicar un perfil.

## Archivos creados por el sistema

- `runs/<run-id>/metadata.json`
- `runs/<run-id>/validation.json`
- `runs/<run-id>/metrics.json`
- `runs/<run-id>/logs/docker-compose.log` cuando se ejecuta `make logs-5g-sa`.

## Cambios comunes

La CLI y la API pueden validar y aplicar perfiles para mantener coherentes los
valores compartidos entre `.env`, Open5GS y RAN/UE. Consulte primero el plan sin
efectos y revise el diff antes de aplicar cambios. La edición manual sigue siendo
posible, pero debe mantener la misma coherencia entre todos los archivos.

Para cambiar un identificador sintético de simulación, use preferentemente el
perfil correspondiente. Si se edita manualmente, deben permanecer coherentes:

- `SUBSCRIBER_IMSI` en `deployments/5g-sa/.env`.
- `supi` en `deployments/5g-sa/ueransim/ue.yaml`.
