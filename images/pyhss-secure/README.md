# Hardened pyHSS Runtime

This small derivative uses a digest-locked pyHSS 1.0.2 base image, packages
the reviewed runtime configuration in the Lain5G-Lab image context and removes
API request-body logging. Lain5G-Lab also
generates a runtime configuration that:

- enables the provisioning key;
- disables insecure AUC reads;
- disables SQLAlchemy SQL echo.

It does not fork or vendor pyHSS source. pyHSS remains an AGPL-3.0 network
service and its source/provenance must remain available with redistributed
images.
