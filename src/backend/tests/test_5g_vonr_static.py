from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
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
        DEPLOY / "scripts" / "status.sh",
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


def test_5g_vonr_status_can_report_stopped_containers_without_local_env():
    status = (DEPLOY / "scripts" / "status.sh").read_text(encoding="utf-8")

    assert 'env_file=.env; [ -f "$scenario_dir/$env_file" ] || env_file=.env.example' in status
    assert 'docker compose --env-file "$env_file"' in status


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
    assert "virtual_call" in validate
    assert "VIRTUAL_CALL_DIALOG_PASS invite=100,180,200 ack=received" in validate
    assert "VIRTUAL_RTP_PASS" in validate


def test_5g_vonr_has_synthetic_phone_call_endpoints_on_its_own_ims_network():
    compose = (DEPLOY / "docker-compose.yml").read_text(encoding="utf-8")
    env = (DEPLOY / ".env.example").read_text(encoding="utf-8")
    init = (DEPLOY / "provisioning" / "ims-subscriber-init.sql").read_text(encoding="utf-8")

    assert "lain5g-lab-5g-vonr-sim-virtual-phones" in compose
    assert "SIP_PHONE_BIND_IP: 10.50.0.32" in compose
    assert "VIRTUAL_PHONE_A_NUMBER=10004" in env
    assert "VIRTUAL_PHONE_B_NUMBER=10001" in env
    assert "__VIRTUAL_PHONE_A_PASSWORD__" in init
    assert "__VIRTUAL_PHONE_B_PASSWORD__" in init


def test_5g_vonr_routes_call_signaling_through_the_ims_chain():
    pcscf = (DEPLOY / "ims" / "pcscf" / "kamailio.cfg").read_text(encoding="utf-8")
    icscf = (DEPLOY / "ims" / "icscf" / "kamailio.cfg").read_text(encoding="utf-8")

    for config in (pcscf, icscf):
        assert 'REGISTER|INVITE|ACK|BYE|CANCEL|MESSAGE' in config
        assert "t_relay()" in config


def test_5g_vonr_status_exports_compose_json_for_the_api():
    status = (DEPLOY / "scripts" / "status.sh").read_text(encoding="utf-8")
    assert "ps --format" in status
    assert '\"Service\":\"{{.Service}}\"' in status


def test_no_forbidden_claims_or_destructive_commands():
    files = list(DEPLOY.rglob("*")) + [ROOT / "Makefile"]
    forbidden = ["docker system prune"]
    for path in files:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for value in forbidden:
            assert value not in text
