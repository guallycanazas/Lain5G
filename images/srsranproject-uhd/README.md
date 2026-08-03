# srsRAN Project UHD Image

Local image for preparing a physical 5G SA gNB with compatible X-Series USRP
hardware.

- Image: `lain5g-lab/srsranproject-uhd:local`
- srsRAN Project: `release_24_10_1`, commit `ef4b0749a12a3b1a8347ae01c937a621603b4069`
- UHD: `v4.10.0.0`

It includes `gnb`, `uhd_find_devices`, `uhd_usrp_probe`, `uhd_config_info`, and `benchmark_rate` when available in the UHD installation.

The image does not download FPGA images, run `uhd_image_loader`, or transmit RF during build or startup. Any FPGA/firmware update is outside the scope of this setup.
