from __future__ import annotations


MONGO_IMAGE = "mongo@sha256:8b6d8f5bbedb25cb73517b65cf99f13aeb75ad5b157a56c479287a840bbad3ac"
MARIADB_IMAGE = "mariadb@sha256:efb4959ef2c835cd735dbc388eb9ad6aab0c78dd64febcd51bc17481111890c4"


IMAGE_CATALOG = {
    "lain5g-lab/open5gs:local": ("gually/lain5g-open5gs:2.7.5-lain1@sha256:d25affe90c39adb35bfef312e725b27d2ef6b139ec1d8b2fe9f5d0da6d82753c", "Core Open5GS 4G/5G"),
    "lain5g-lab/ueransim:local": ("gually/lain5g-ueransim:3.2.6-lain1@sha256:1451cb0327f97fb276b30b78ec1c3ad54bbb480ec044004e580e62a20b60a8a2", "Simulated 5G gNB and UE"),
    "lain5g-lab/srsran4g-sim:local": ("gually/lain5g-srsran4g-sim:23.11-lain1@sha256:7ec771cf70e77f699283017b02bbe6311fd377047109dc952c2c18ebae1e2ced", "Simulated 4G eNB and UE"),
    "lain5g-lab/srsran4g-uhd:local": ("gually/lain5g-srsran4g-uhd:23.11-uhd4.10-lain1@sha256:8d8ed84133008b542e0db510d57a458049c1b6391e7fd557a81d03dde794cb2e", "srsRAN 4G with UHD/X-Series"),
    "lain5g-lab/srsranproject-uhd:local": ("gually/lain5g-srsranproject-uhd:24.10.1-uhd4.10-lain1@sha256:a7f08617cfdd5611c7988f58cd8463836e61610048aa29218c657730018f0711", "srsRAN Project with UHD/X-Series"),
    "lain5g-lab/kamailio:local": ("gually/lain5g-kamailio:5.8.8-lain1@sha256:a59ac70c28c9635944b4bbebbfd292e611b08b2b454bcb0f020afc3d4544ca0e", "SIP/IMS services"),
    "lain5g-lab/ims-dns:local": ("gually/lain5g-ims-dns:1.11.3-lain1@sha256:54663afe89d68dab67d5b0d98a70d6e2d2f7910ea9267622d8844a2ce9fdaed7", "DNS for IMS"),
    "lain5g-lab/ims-sip:local": ("gually/lain5g-ims-sip:1.0-lain1@sha256:fa164401efcab1738c8b8e56ade75949ae50e25e2745a37053d7d3c8ebf295cf", "Laboratory SIP tools"),
}

PROFILE_IMAGES = {
    "4g-lte-sim": ("lain5g-lab/open5gs:local", "lain5g-lab/srsran4g-sim:local", MONGO_IMAGE),
    "4g-volte-sim": ("lain5g-lab/open5gs:local", "lain5g-lab/srsran4g-sim:local", "lain5g-lab/kamailio:local", "lain5g-lab/ims-dns:local", "lain5g-lab/ims-sip:local", MONGO_IMAGE, MARIADB_IMAGE),
    "4g-lte-x310": ("lain5g-lab/open5gs:local", "lain5g-lab/srsran4g-uhd:local", "lain5g-lab/kamailio:local", "lain5g-lab/ims-dns:local", MONGO_IMAGE, MARIADB_IMAGE),
    "5g-sa": ("lain5g-lab/open5gs:local", "lain5g-lab/ueransim:local", MONGO_IMAGE),
    "5g-sa-x310": ("lain5g-lab/open5gs:local", "lain5g-lab/srsranproject-uhd:local", MONGO_IMAGE),
    "5g-nsa-x310": ("lain5g-lab/open5gs:local", "lain5g-lab/srsran4g-uhd:local", "lain5g-lab/kamailio:local", "lain5g-lab/ims-dns:local", MONGO_IMAGE, MARIADB_IMAGE),
    "5g-vonr": ("lain5g-lab/open5gs:local", "lain5g-lab/ueransim:local", "lain5g-lab/kamailio:local", "lain5g-lab/ims-dns:local", "lain5g-lab/ims-sip:local", MONGO_IMAGE, MARIADB_IMAGE),
}

RF_ACCESS_IMAGES = {
    "4g-lte-x310": "lain5g-lab/srsran4g-uhd:local",
    "5g-sa-x310": "lain5g-lab/srsranproject-uhd:local",
    "5g-nsa-x310": "lain5g-lab/srsran4g-uhd:local",
}


def required_images(profile_id: str, core_only: bool = False) -> list[str]:
    if profile_id == "all":
        images = list(IMAGE_CATALOG) + [MONGO_IMAGE, MARIADB_IMAGE]
    elif profile_id in PROFILE_IMAGES:
        images = list(PROFILE_IMAGES[profile_id])
        if core_only and profile_id in RF_ACCESS_IMAGES:
            images.remove(RF_ACCESS_IMAGES[profile_id])
    else:
        raise ValueError(f"Unknown image profile: {profile_id}")
    return list(dict.fromkeys(images))
