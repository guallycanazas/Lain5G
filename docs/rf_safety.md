# RF Safety

The X-Series USRP RF paths are blocked by default. No target may transmit RF
without explicit authorization from the lab operator.

## Rules

- Do not transmit in licensed bands without legal and technical authorization.
- Use a cabled, shielded, or formally authorized environment.
- In cabled mode, use appropriate attenuation; the example requires at least 60 dB.
- Define a finite maximum duration; the example uses 60 seconds.
- Keep `auto_stop: true`.
- Do not run `docker system prune` as part of these workflows.
- Do not update FPGA images or firmware automatically.

## Local RF Files Excluded from Version Control

```bash
cp deployments/4g-volte/x310/rf/channel-plan.example.yaml deployments/4g-volte/x310/rf/channel-plan.yaml
cp deployments/4g-volte/x310/rf/safety-manifest.example.yaml deployments/4g-volte/x310/rf/safety-manifest.yaml
```

Edit both files before any RF operation. The actual files are ignored by Git.

## Emergency Stop

```bash
make emergency-stop-4g-lte-x310
```

This target removes the local active-RF marker and stops only `enb-x310`.
