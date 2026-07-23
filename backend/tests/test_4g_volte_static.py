from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEPLOY = ROOT / "deployments" / "4g-volte"


def test_required_4g_files_exist():
    required = [
        DEPLOY / "common" / ".env.example",
        DEPLOY / "common" / "open5gs" / "mme.yaml",
        DEPLOY / "sim" / "docker-compose.yml",
        DEPLOY / "x310" / "docker-compose.yml",
        DEPLOY / "x310" / "rf" / "safety-manifest.example.yaml",
        DEPLOY / "x310" / "rf" / "channel-plan.example.yaml",
        ROOT / "images" / "srsran4g-sim" / "Dockerfile",
        ROOT / "images" / "ims-sip" / "Dockerfile",
        ROOT / "images" / "srsran4g-uhd" / "Dockerfile",
    ]
    missing = [str(path) for path in required if not path.exists()]
    assert missing == []


def test_4g_compose_projects_are_isolated():
    sim = (DEPLOY / "sim" / "docker-compose.yml").read_text(encoding="utf-8")
    x310 = (DEPLOY / "x310" / "docker-compose.yml").read_text(encoding="utf-8")
    assert "lain5g-lab-4g-volte-sim" in sim
    assert "lain5g-lab-4g-lte-x310" in x310
    assert "lain5g-lab-5g-sa" not in sim
    assert "lain5g-lab-5g-sa" not in x310


def test_x310_rf_profile_is_explicit_and_safe_by_default():
    compose = (DEPLOY / "x310" / "docker-compose.yml").read_text(encoding="utf-8")
    manifest = (DEPLOY / "x310" / "rf" / "safety-manifest.example.yaml").read_text(encoding="utf-8")
    channel = (DEPLOY / "x310" / "rf" / "channel-plan.example.yaml").read_text(encoding="utf-8")
    assert "profiles: [\"rf\"]" in compose
    assert "authorization_confirmed: false" in manifest
    assert "auto_stop: true" in manifest
    assert "maximum_duration_seconds: 60" in manifest
    assert "downlink_frequency_hz:\n" in channel
    assert "uplink_frequency_hz:\n" in channel


def test_scripts_do_not_update_fpga_or_prune_docker():
    scripts = list((DEPLOY / "x310" / "scripts").glob("*.sh")) + list((DEPLOY / "sim" / "scripts").glob("*.sh"))
    for script in scripts:
        text = script.read_text(encoding="utf-8")
        assert "docker system prune" not in text
        assert "uhd_image_loader" not in text


def test_x310_rf_start_requires_guardrails():
    start_enb = (DEPLOY / "x310" / "scripts" / "start-enb.sh").read_text(encoding="utf-8")
    uhd_check = (DEPLOY / "x310" / "scripts" / "uhd-check.sh").read_text(encoding="utf-8")
    hardware_check = (DEPLOY / "x310" / "scripts" / "hardware-check.sh").read_text(encoding="utf-8")
    assert "LAIN5G_ALLOW_RF_START" in start_enb
    assert "preflight.sh" in start_enb
    assert "maximum_duration_seconds" in start_enb
    assert "stop enb-x310" in start_enb
    assert 'grep -Fxq "run_id=$run_id"' in start_enb
    assert "sleep 5" in start_enb
    assert ".State.Running" in start_enb
    assert "--network host" in uhd_check
    assert "uhd_usrp_probe" in uhd_check
    assert "uhd_find_devices" in hardware_check


def test_x310_uses_profile_specific_addresses():
    compose = (DEPLOY / "x310" / "docker-compose.yml").read_text(encoding="utf-8")
    enb = (DEPLOY / "x310" / "ran" / "enb.conf").read_text(encoding="utf-8")
    assert "./open5gs/mme.yaml" in compose
    assert "./ims/pcscf/kamailio.cfg" in compose
    assert "mme_addr = 172.22.0.9" in enb
    assert "s1c_bind_addr = 172.22.0.1" in enb
    assert "gtp_bind_addr = 172.22.0.1" in enb
    for path in (DEPLOY / "x310" / "open5gs").glob("*.yaml"):
        text = path.read_text(encoding="utf-8")
        assert "10.41." not in text


def test_x310_supports_ims_signaling_bearer():
    rb = (DEPLOY / "x310" / "ran" / "rb.conf").read_text(encoding="utf-8")
    assert "qci = 5;" in rb


def test_secret_values_are_not_committed_in_env_example():
    env = (DEPLOY / "common" / ".env.example").read_text(encoding="utf-8")
    assert "SUBSCRIBER_KEY=\n" in env
    assert "SUBSCRIBER_OPC=\n" in env
    assert "IMS_AUTH_PASSWORD=\n" in env
