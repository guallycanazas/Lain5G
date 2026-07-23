from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEPLOY = ROOT / "deployments" / "5g-sa-x310"
IMAGE = ROOT / "images" / "srsranproject-uhd"


def test_required_5g_x310_files_exist():
    required = [
        IMAGE / "Dockerfile",
        IMAGE / "entrypoint.sh",
        IMAGE / "uhd-4.10-event-code-ok.patch",
        IMAGE / "README.md",
        DEPLOY / "docker-compose.yml",
        DEPLOY / ".env.example",
        DEPLOY / "open5gs" / "amf.yaml",
        DEPLOY / "open5gs" / "smf.yaml",
        DEPLOY / "gnb" / "gnb_x310.yml",
        DEPLOY / "rf" / "channel-plan.example.yaml",
        DEPLOY / "rf" / "safety-manifest.example.yaml",
        DEPLOY / "scripts" / "hardware-check.sh",
        DEPLOY / "scripts" / "preflight.sh",
        DEPLOY / "scripts" / "start-core.sh",
        DEPLOY / "scripts" / "start-gnb.sh",
        DEPLOY / "scripts" / "stop.sh",
        DEPLOY / "scripts" / "emergency-stop.sh",
        ROOT / "docs" / "5g_x310_cots_ue_checklist.md",
    ]
    assert [str(path) for path in required if not path.exists()] == []


def test_srsran_project_image_is_pinned_and_safe():
    dockerfile = (IMAGE / "Dockerfile").read_text(encoding="utf-8")
    entrypoint = (IMAGE / "entrypoint.sh").read_text(encoding="utf-8")
    assert "SRSRAN_PROJECT_REF=release_24_10_1" in dockerfile
    assert "SRSRAN_PROJECT_COMMIT=ef4b0749a12a3b1a8347ae01c937a621603b4069" in dockerfile
    assert "UHD_VERSION=v4.10.0.0" in dockerfile
    assert "-DENABLE_C_API=ON" in dockerfile
    assert "-DUHD_INCLUDE_DIRS=/usr/local/include" in dockerfile
    assert "uhd-4.10-event-code-ok.patch" in dockerfile
    assert "libuhd" in dockerfile
    assert "gnb --version" in dockerfile
    assert "uhd_config_info --version" in dockerfile
    assert "uhd_image_loader" not in entrypoint


def test_compose_is_isolated_and_rf_profile_only():
    compose = (DEPLOY / "docker-compose.yml").read_text(encoding="utf-8")
    assert "name: lain5g-lab-5g-sa-x310" in compose
    assert "profiles: [\"rf\"]" in compose
    assert "network_mode: host" in compose
    assert "cap_add: [SYS_NICE, SYS_RESOURCE]" in compose
    assert "rtprio: 99" in compose
    assert "privileged" not in compose
    assert "lain5g-lab/ueransim" not in compose
    assert "./open5gs/amf.yaml" in compose
    assert "./open5gs/smf.yaml" in compose


def test_env_example_does_not_commit_rf_values_or_secrets():
    env = (DEPLOY / ".env.example").read_text(encoding="utf-8")
    for name in ["DL_ARFCN", "NR_BAND", "TX_GAIN", "RX_GAIN", "AMF_ADDR", "GNB_BIND_ADDR", "N3_BIND_ADDR"]:
        assert f"{name}=\n" in env
    forbidden = ["SUBSCRIBER_KEY", "SUBSCRIBER_OPC", "KI=", "K=", "OPC="]
    for item in forbidden:
        assert item not in env


def test_gnb_config_targets_x310_and_open5gs_mapping():
    gnb = (DEPLOY / "gnb" / "gnb_x310.yml").read_text(encoding="utf-8")
    assert "device_driver: uhd" in gnb
    assert "device_args: type=${USRP_TYPE},addr=${USRP_ADDR}" in gnb
    assert "addr: ${AMF_ADDR}" in gnb
    assert "plmn: \"${MCC}${MNC}\"" in gnb
    assert "channel_bandwidth_MHz: ${CHANNEL_BANDWIDTH_MHZ}" in gnb
    assert "srate: ${SAMPLE_RATE_MHZ}" in gnb


def test_rf_start_requires_guardrails_and_scripts_are_non_destructive():
    start_core = (DEPLOY / "scripts" / "start-core.sh").read_text(encoding="utf-8")
    start = (DEPLOY / "scripts" / "start-gnb.sh").read_text(encoding="utf-8")
    preflight = (DEPLOY / "scripts" / "preflight.sh").read_text(encoding="utf-8")
    hardware = (DEPLOY / "scripts" / "hardware-check.sh").read_text(encoding="utf-8")
    assert "ip route replace" in start_core
    assert "lain5g-lab-5g-sa-x310-upf" in start_core
    assert "LAIN5G_ALLOW_5G_RF_START" in start
    assert "sleep 5" in start
    assert ".State.Running" in start
    assert "REQUIRE_RF_READY=true" in start
    assert "cpupower frequency-set -g performance" in start
    assert "authorization_confirmed" in preflight
    assert "gnb_uhd_link" in preflight
    assert "uhd_find_devices" in hardware
    assert "uhd_usrp_probe" in hardware
    for script in (DEPLOY / "scripts").glob("*.sh"):
        text = script.read_text(encoding="utf-8")
        assert "docker system prune" not in text
        assert "uhd_image_loader" not in text


def test_5g_scenarios_stop_each_other_and_release_the_shared_address_space():
    stop = (DEPLOY / "scripts" / "stop.sh").read_text(encoding="utf-8")
    start_core = (DEPLOY / "scripts" / "start-core.sh").read_text(encoding="utf-8")
    simulation_start = (ROOT / "deployments/5g-sa/scripts/start.sh").read_text(encoding="utf-8")
    simulation_stop = (ROOT / "deployments/5g-sa/scripts/stop.sh").read_text(encoding="utf-8")
    assert "down --remove-orphans" in stop
    assert "down --remove-orphans" in simulation_stop
    assert 'x310_project="lain5g-lab-5g-sa-x310"' in simulation_start
    assert 'deployments/5g-sa-x310/scripts/stop.sh' in simulation_start
    assert 'simulation_project="lain5g-lab-5g-sa"' in start_core
    assert 'deployments/5g-sa/scripts/stop.sh' in start_core
    assert "Removed stopped 5G SA containers with stale network references" in simulation_start
