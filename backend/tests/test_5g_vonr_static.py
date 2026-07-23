from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEPLOY = ROOT / "deployments" / "5g-vonr"


def test_required_5g_vonr_files_exist():
    required = [
        DEPLOY / "docker-compose.yml",
        DEPLOY / ".env.example",
        DEPLOY / "open5gs" / "nrf.yaml",
        DEPLOY / "open5gs" / "amf.yaml",
        DEPLOY / "open5gs" / "smf.yaml",
        DEPLOY / "open5gs" / "upf.yaml",
        DEPLOY / "ueransim" / "gnb.yaml",
        DEPLOY / "ueransim" / "ue-internet.yaml",
        DEPLOY / "ueransim" / "ue-ims.yaml",
        DEPLOY / "provisioning" / "open5gs-subscriber-init.js",
        DEPLOY / "provisioning" / "ims-subscriber-init.sql",
        DEPLOY / "scripts" / "validate.sh",
    ]
    missing = [str(path) for path in required if not path.exists()]
    assert missing == []


def test_5g_vonr_compose_is_isolated():
    compose = (DEPLOY / "docker-compose.yml").read_text(encoding="utf-8")
    assert "name: lain5g-lab-5g-vonr-sim" in compose
    assert "lain5g-lab-5g-sa" not in compose
    assert "lain5g-lab-4g-volte-sim" not in compose
    assert "lain5g-lab-4g-lte-x310" not in compose
    assert "network_mode: \"service:ue\"" in compose


def test_5g_vonr_env_example_has_no_secrets():
    env = (DEPLOY / ".env.example").read_text(encoding="utf-8")
    assert "SUBSCRIBER_KEY=\n" in env
    assert "SUBSCRIBER_OPC=\n" in env
    assert "IMS_AUTH_PASSWORD=\n" in env


def test_5g_vonr_provisions_two_dnn_sessions():
    smf = (DEPLOY / "open5gs" / "smf.yaml").read_text(encoding="utf-8")
    upf = (DEPLOY / "open5gs" / "upf.yaml").read_text(encoding="utf-8")
    ue = (DEPLOY / "ueransim" / "ue-ims.yaml").read_text(encoding="utf-8")
    provisioner = (DEPLOY / "provisioning" / "open5gs-subscriber-init.js").read_text(encoding="utf-8")
    for text in (smf, upf, ue, provisioner):
        assert "internet" in text
        assert "ims" in text
    assert "10.60.0.0/16" in smf
    assert "10.61.0.0/16" in smf


def test_5g_vonr_validation_requires_sip_challenge_and_ims_path():
    validate = (DEPLOY / "scripts" / "validate.sh").read_text(encoding="utf-8")
    assert "SIP_CLIENT_CHALLENGE_RECEIVED code=401" in validate
    assert "SIP_CLIENT_FINAL_RESPONSE code=200" in validate
    assert "pcscf_reachable_over_ims" in validate
    assert "ip route replace" in validate


def test_no_forbidden_claims_or_destructive_commands():
    files = list(DEPLOY.rglob("*")) + [ROOT / "Makefile"]
    forbidden = ["docker system prune"]
    for path in files:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for value in forbidden:
            assert value not in text
