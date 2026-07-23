# srsRAN Project UHD Image

Imagen local para preparar un gNB 5G SA físico con USRP X310.

- Imagen: `lain5g-lab/srsranproject-uhd:local`
- srsRAN Project: `release_24_10_1`, commit `ef4b0749a12a3b1a8347ae01c937a621603b4069`
- UHD: `v4.10.0.0`

Incluye `gnb`, `uhd_find_devices`, `uhd_usrp_probe`, `uhd_config_info` y `benchmark_rate` cuando está disponible en la instalación UHD.

La imagen no descarga imágenes FPGA, no ejecuta `uhd_image_loader` y no transmite RF durante build o arranque. Cualquier actualización de FPGA/FW queda fuera de esta preparación.
