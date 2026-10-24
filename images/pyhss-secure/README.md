# OpenLain5G pyHSS Image

This image builds pyHSS 1.0.2 from the pinned upstream source commit recorded
in `deployments/ims-real/images.lock.yaml`, on a digest-pinned Ubuntu base. It
does not use a third-party pyHSS container image. The pyHSS source is AGPL-3.0;
redistribution must include the corresponding source and license.

OpenLain5G packages the reviewed runtime configuration and generates a
runtime-only configuration that:

- enables the provisioning key;
- disables insecure AUC reads;
- disables SQLAlchemy SQL echo.

Provisioning credentials are accepted only by the internal pyHSS API and are
not logged. The API and Diameter listeners remain unexposed on the host.
