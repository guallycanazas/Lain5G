# Versioned PDF user manuals

Each supported software release should keep its user manual source and compiled
PDF in a version-specific folder, for example `v1.1.9/`. The manual version
identifies the software release it describes.

Update the manual when an operator-visible workflow, requirement, page, profile,
or recovery step changes. Internal code changes that do not affect user tasks do
not require rewriting the guide. Recheck all steps against the source candidate
and capture current UI screens for each release. If the exact release cannot be
run in the browser, label the screenshots with the version actually shown and
do not present them as release verification.

Keep the `.tex` source, image assets, and final PDF together. For a release,
verify that the PDF cover, metadata, directory, filename, and release notes all
carry the same version. The v1.1.9 candidate PDF was built with Tectonic 0.17.0,
the pinned Tectonic v33 bundle (SHA-256
`6ffe055852f8faf66c0acbe1a7fb27f87b869a90bad1204f3bf4d9683f597c7c`), and a
fixed timestamp. Keep the timestamp fixed for this edition; choose and record a
new timestamp when producing a later edition. This makes repeated builds
byte-for-byte reproducible.

```sh
cd docs/manual/v1.1.9
test "$(tectonic --version)" = "Tectonic 0.17.0"
SOURCE_DATE_EPOCH=1794087493 tectonic \
  --bundle https://relay.fullyjustified.net/default_bundle_v33.tar \
  --outdir ../../../output/pdf main.tex
cp ../../../output/pdf/main.pdf OpenLain5G-User-Manual-v1.1.9.pdf
cp ../../../output/pdf/main.pdf ../../../output/pdf/OpenLain5G-User-Manual-v1.1.9.pdf
sha256sum OpenLain5G-User-Manual-v1.1.9.pdf
# Expected: 8cde2a13ddbcd8edba3abba48d04a66c34782bbb0f6e5ceb1ce0cefffeaae086
```

The manual build is a documentation task. It is not a prerequisite for
`install.sh`, the application Docker images, or `make softwarex-check`.
