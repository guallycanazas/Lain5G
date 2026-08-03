# srsRAN 4G UHD Image

Image for `srsenb` with UHD and compatible X-Series USRP hardware.

- srsRAN 4G: `release_23_11`
- UHD: `v4.10.0.0`

The image includes `uhd_find_devices`, `uhd_usrp_probe`, and `uhd_image_loader`, but does not automatically download or update FPGA images at startup.

Any FPGA/firmware update is outside the scope of this deliverable and requires explicit authorization.
