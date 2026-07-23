# RF Safety

La ruta X310 está bloqueada por defecto. Ningún target debe transmitir RF sin autorización explícita del operador del laboratorio.

## Reglas

- No transmitir en bandas licenciadas sin permiso legal y técnico.
- Usar entorno cabled, shielded o formalmente autorizado.
- En modo cabled, usar atenuación adecuada; el ejemplo exige al menos 60 dB.
- Definir duración máxima finita; el ejemplo usa 60 segundos.
- Mantener `auto_stop: true`.
- No ejecutar `docker system prune` como parte de estos flujos.
- No actualizar FPGA ni firmware automáticamente.

## Archivos Reales No Versionados

```bash
cp deployments/4g-volte/x310/rf/channel-plan.example.yaml deployments/4g-volte/x310/rf/channel-plan.yaml
cp deployments/4g-volte/x310/rf/safety-manifest.example.yaml deployments/4g-volte/x310/rf/safety-manifest.yaml
```

Edita ambos archivos antes de cualquier ejecución RF. Los archivos reales están ignorados por Git.

## Parada De Emergencia

```bash
make emergency-stop-4g-lte-x310
```

Este target elimina el marcador local de RF activa y detiene solo `enb-x310`.
