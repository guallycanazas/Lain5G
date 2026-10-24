# OpenLain5G Real IMS Package

This directory contains the target-owned Compose and provenance layer for a
real Open5GS, Kamailio, and pyHSS IMS core. Open5GS and Kamailio are built by
OpenLain5G from pinned upstream source; pyHSS is built from its pinned source
release. MariaDB, DNS, and RTPengine use OpenLain5G-owned image recipes with
vendor packages and pinned base references. No Herlesupreeth container image
is used. His repository remains a documented reference for the IMS topology and
role configuration. See `images.lock.yaml` for source and base provenance.

This package is operated through the local `/ims` console and its `/api/ims-real`
backend routes. It has no standalone CLI entry point. Runtime secrets and
generated pyHSS configuration remain excluded under the ignored
`deployments/ims-real/.runtime/` directory.

Use **Preparation** to build missing first-party IMS images on the local Docker
host from the checked-in `images/` contexts. Existing local images are reused.
The user does not need to publish these images to Docker Hub or another
registry. Docker may download pinned base images and build dependencies from
their upstream sources; the OpenLain5G images themselves remain local. **Start
runtime** checks that preparation is complete, then starts the selected core and
IMS services.

The manifests publish no host ports. In particular, the pyHSS API and Diameter
listeners are reachable only inside the Compose project. Named volumes and the
default network remain Compose-scoped, and 4G and 5G use distinct
`lain5g-lab-ims-real-*` projects and backend-supplied subnet overrides.

This package starts no RF service and contains no RAN or UERANSIM. The console
is a separate UI for operating Open5GS + Kamailio + pyHSS; it does not replace
the Open5GS-only `/subscribers` page. Core readiness, UE registration, and
voice/media operation are separate correlated validation layers; see
`docs/real_ims.md` for the validation scope.
