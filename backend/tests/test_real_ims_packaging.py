from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEPLOY = ROOT / "deployments" / "ims-real"
IMAGE_CONTEXTS = {
    "ims-real-open5gs": ("441d40e16f76ae79fc25eaaa92245850ed833bdd3d0d0dc78acbffd958cdc2c6", "MIT AND AGPL-3.0-only AND BSD-2-Clause"),
    "ims-real-kamailio": ("67dc92b423ca5ef0b827a049d0cabeff741f3eafd9222608036494f4d7611821", "MIT AND GPL-2.0-only AND BSD-2-Clause"),
    "ims-real-dns": ("0e0a0fc6d18feda9db1590da249ac93e8d5abfea8f4c3c0c849ce512b5ef8982", "MIT AND BSD-2-Clause"),
    "ims-real-mysql": ("324d3d4c5089feea787684f0dbf1a646dde8d356170085ac0b6538aee6910057", "MIT AND GPL-2.0-only AND BSD-2-Clause"),
    "ims-real-rtpengine": ("60eac759739651111db372c07be67863818726f754804b8707c90979bda511df", "MIT AND GPL-3.0-only AND BSD-2-Clause"),
    "pyhss-secure": ("90206eb3cbe862bfa71e0bfaf038fe3ddbefba1df531eb2157c9642ac732e6fb", "MIT AND AGPL-3.0-only AND BSD-2-Clause"),
}


def test_real_ims_compose_is_scoped_and_unpublished() -> None:
    for mode in ("4g", "5g"):
        raw = (DEPLOY / f"compose.{mode}.yaml").read_text(encoding="utf-8")
        assert raw.startswith(f"name: lain5g-lab-ims-real-{mode}\n")
        assert "lain5g/" not in raw
        assert "container_name:" not in raw
        assert "ports:" not in raw
        assert "ueransim" not in raw.lower()
        assert "webui" not in raw.lower()
        assert "  pyhss:\n" in raw
        assert "\n    name:" not in raw


def test_real_ims_environment_is_minimal_and_non_secret() -> None:
    raw = (DEPLOY / "env.defaults").read_text(encoding="utf-8")
    values = {
        key: value
        for line in raw.splitlines()
        if line and not line.startswith("#")
        for key, value in [line.split("=", 1)]
    }
    required = {
        "LAIN5G_IMS_ENV_FILE", "MCC", "MNC", "TAC", "NETWORK_NAME",
        "TEST_NETWORK", "MONGO_IP",
        "HSS_IP", "PCRF_IP", "PCRF_BIND_PORT", "PCRF_PUB_IP", "SGWC_IP",
        "SGWU_IP", "SGWU_ADVERTISE_IP", "SMF_IP", "SMF_DNS1", "SMF_DNS2",
        "UPF_IP", "UPF_ADVERTISE_IP", "UPF_TUNTAP_MODE",
        "UPF_INTERNET_APN_IF_NAME", "UPF_IMS_APN_IF_NAME", "MME_IP", "AMF_IP",
        "AUSF_IP", "NRF_IP", "UDM_IP", "UDR_IP", "DNS_IP", "RTPENGINE_IP",
        "MYSQL_IP", "PYHSS_IP", "PYHSS_BIND_PORT", "ICSCF_IP",
        "ICSCF_BIND_PORT", "SCSCF_IP", "SCSCF_BIND_PORT", "PCSCF_IP",
        "PCSCF_PUB_IP", "PCSCF_BIND_PORT", "PCF_IP", "NSSF_IP", "BSF_IP",
        "SCP_IP", "UE_IPV4_INTERNET", "UE_IPV4_IMS", "MAX_NUM_UE",
        "DOCKER_HOST_IP", "ENTITLEMENT_SERVER_IP", "OSMOMSC_IP", "SMSC_IP",
        "IBCF_IP", "OCS_IP", "OCS_BIND_PORT", "OSMOEPDG_IP",
    }
    assert required <= values.keys()
    assert values["DOCKER_HOST_IP"] == "127.0.0.1"
    forbidden_prefixes = ("UE1_", "GRAFANA_", "WEBUI_", "METRICS_", "NR_UE_", "NR_GNB_")
    assert not any(key.startswith(forbidden_prefixes) for key in values)
    assert not any(key in values for key in ("KI", "K", "OP", "OPC", "IMSI", "IMEI"))
    assert "/home/" not in raw


def test_real_ims_provenance_hashes_match_target_files() -> None:
    provenance = json.loads((DEPLOY / "config-provenance.json").read_text(encoding="utf-8"))
    assert provenance["source_commit"] == "3685b58aa0c7c28b2fecc6b9533f128285bf8dda"
    assert provenance["license"] == "BSD-2-Clause"
    assert provenance["files"]
    for entry in provenance["files"]:
        assert entry["path"].startswith("images/")
        assert "ueransim" not in entry["path"].lower()
        target = ROOT / entry["path"]
        assert target.is_file(), entry["path"]
        assert hashlib.sha256(target.read_bytes()).hexdigest() == entry["sha256"], entry["path"]


def test_real_ims_outer_images_use_target_namespace_and_locked_bases() -> None:
    lock = (DEPLOY / "images.lock.yaml").read_text(encoding="utf-8")
    assert "lain5g-lab/" in lock
    assert "lain5g/" not in lock
    assert "ueransim" not in lock.lower()
    assert "mongo@sha256:8b6d8f5bbedb25cb73517b65cf99f13aeb75ad5b157a56c479287a840bbad3ac" in lock
    for context, (digest, licenses) in IMAGE_CONTEXTS.items():
        dockerfile = (ROOT / "images" / context / "Dockerfile").read_text(encoding="utf-8")
        assert "guallycanazas/Lain5G-Lab" in dockerfile
        assert "guallycanazas/Lain5G\"" not in dockerfile
        assert f'org.opencontainers.image.licenses="{licenses}"' in dockerfile
        assert f"@sha256:{digest}" in dockerfile
        assert digest in lock
