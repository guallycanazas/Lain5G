from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEPLOY = ROOT / "deployments" / "4g-lte-sim"


def test_lte_simulation_files_exist():
    required = [
        DEPLOY / "docker-compose.yml",
        DEPLOY / "open5gs" / "mme.yaml",
        DEPLOY / "open5gs" / "pgwc.yaml",
        DEPLOY / "ran" / "enb.conf",
        DEPLOY / "ran" / "ue.conf",
        DEPLOY / "scripts" / "start.sh",
        DEPLOY / "scripts" / "validate.sh",
        ROOT / "config" / "profiles" / "4g-lte-sim.yaml",
    ]
    assert [str(path) for path in required if not path.exists()] == []


def test_lte_simulation_is_isolated_from_volte():
    compose = (DEPLOY / "docker-compose.yml").read_text(encoding="utf-8")
    assert "name: lain5g-lab-4g-lte-sim" in compose
    assert "subnet: 10.43.0.0/24" in compose
    assert "lain5g-lab-4g-lte-sim-mongo-data" in compose
    for service in ["ims-database", "pcscf", "icscf", "scscf", "dns", "sip-register"]:
        assert f"  {service}:" not in compose


def test_lte_simulation_uses_srsenb_and_srsue_over_zmq():
    compose = (DEPLOY / "docker-compose.yml").read_text(encoding="utf-8")
    enb = (DEPLOY / "ran" / "enb.conf").read_text(encoding="utf-8")
    ue = (DEPLOY / "ran" / "ue.conf").read_text(encoding="utf-8")
    assert 'command: ["srsenb"' in compose
    assert 'command: ["srsue"' in compose
    assert "device_name = zmq" in enb
    assert "device_name = zmq" in ue
    assert "mme_addr = 10.43.0.10" in enb


def test_lte_simulation_provisions_only_internet_apn():
    pgwc = (DEPLOY / "open5gs" / "pgwc.yaml").read_text(encoding="utf-8")
    subscriber = (DEPLOY / "provisioning" / "open5gs-subscriber-init.js").read_text(encoding="utf-8")
    assert "dnn: internet" in pgwc
    assert "dnn: ims" not in pgwc
    assert "APN_IMS" not in subscriber


def test_lte_simulation_scripts_never_start_rf():
    for script in (DEPLOY / "scripts").glob("*.sh"):
        text = script.read_text(encoding="utf-8")
        assert "uhd_usrp_probe" not in text
        assert "LAIN5G_ALLOW_RF_START" not in text
        assert "docker system prune" not in text


def test_lte_simulation_validation_bounds_growing_logs():
    validate = (DEPLOY / "scripts" / "validate.sh").read_text(encoding="utf-8")
    assert "timeout 10s docker compose" in validate
    assert "grep -Eiq -m1" in validate
