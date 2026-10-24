# OpenLain5G Visual Assets

Web-delivery assets in this directory were derived from the PNG artwork in the
user-supplied `lain5g-landing-assets-v2` package. The original PNG files remain
the high-quality sources; the website uses optimized WebP variants.

Console placements:

- `control-plane-topology.webp`: consistent overview art for the dashboard and
  landing page; labels and runtime status are rendered by the application.
- `scenario-workflow.webp`: scenario and deployment workflow; contains no
  runtime claims.
- `host-preparation-v2.webp`: Linux workstation, SDR radio, and local service
  containers for host readiness.
- `logs-investigation-v2.webp`: log viewer and service fault tracing; contains
  no live log data.
- `metrics-observability.webp`: spectrum and telemetry concepts; the artwork
  contains no values and does not imply live RF telemetry.
- `rf-isolation.webp`: cabled lab bench, attenuation path, and shielded test
  enclosure; actual enforcement remains in local manifests and backend checks.
- `voice-topology.webp`: IMS workspace concept; validation claims come from the
  scenario run evidence, not from the illustration itself.
- `subscriber-provisioning.webp`: subscriber workflow; eSIM remains a design
  concept and is not exposed by the current backend.
- `sdr-hardware.webp`: cropped to the guarded USRP preparation path.
- `observability-concept.webp`: illustrative dashboard; displayed values are
  not live telemetry.
- `lab-recipes.webp`: reproducible 4G/5G and VoLTE/VoNR workflow.
- `isolation-concept.webp`: isolation artwork; actual enforcement remains in
  local manifests, preflight checks, and backend guardrails.

`lain-avatar.webp` is the user-selected OpenLain5G emblem. Third-party project marks
are documented separately in `logos/README.md`.
