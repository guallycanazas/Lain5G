from __future__ import annotations

import json
import os
import shlex
import subprocess
from pathlib import Path

import pytest


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


def test_lte_simulation_runtime_renderer_matches_provisioned_credentials(tmp_path: Path):
    template = DEPLOY / "ran" / "ue.conf"
    entrypoint = (ROOT / "images/srsran4g-sim/entrypoint.sh").read_text(encoding="utf-8")
    runtime_config = tmp_path / "runtime-ue.conf"
    captured_config = tmp_path / "captured-ue.conf"
    executable_dir = tmp_path / "bin"
    executable_dir.mkdir()
    srsue = executable_dir / "srsue"
    srsue.write_text('#!/bin/sh\ncp "$1" "$CAPTURED_CONFIG"\n', encoding="utf-8")
    srsue.chmod(0o755)
    entrypoint = entrypoint.replace("runtime_conf=/tmp/lain5g-srsue.conf", f"runtime_conf={shlex.quote(str(runtime_config))}")
    entrypoint = entrypoint.replace("/etc/srsran/ue.conf", str(template))
    credentials = {
        "SUBSCRIBER_IMSI": "001010000000001",
        "SUBSCRIBER_KEY": "00112233445566778899AABBCCDDEEFF",
        "SUBSCRIBER_OPC": "FFEEDDCCBBAA99887766554433221100",
    }
    environment = {
        **os.environ,
        **credentials,
        "CAPTURED_CONFIG": str(captured_config),
        "PATH": f"{executable_dir}:{os.environ['PATH']}",
    }

    result = subprocess.run(
        ["bash", "-c", entrypoint, "entrypoint", "srsue", str(template)],
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    values = {
        key.strip(): value.strip()
        for line in captured_config.read_text(encoding="utf-8").splitlines()
        if "=" in line
        for key, value in [line.split("=", 1)]
    }
    assert values["imsi"] == credentials["SUBSCRIBER_IMSI"]
    assert values["k"] == credentials["SUBSCRIBER_KEY"]
    assert values["opc"] == credentials["SUBSCRIBER_OPC"]
    assert "00000000000000000000000000000000" not in template.read_text(encoding="utf-8")


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


def test_lte_simulation_validation_waits_for_attach_and_proves_user_plane():
    validate = (DEPLOY / "scripts" / "validate.sh").read_text(encoding="utf-8")

    assert "for _ in 1 2 3 4 5 6" in validate
    assert "Number of MME-Sessions is now [1-9][0-9]*" in validate
    assert "ip -o -4 addr show dev tun_srsue" in validate
    assert "ip link show dev tun_srsue" in validate
    assert "ping -I tun_srsue -c 3" in validate


def test_5g_simulation_validation_uses_scenario_run_and_waits_for_registration():
    validate = (ROOT / "deployments/5g-sa/scripts/validate.sh").read_text(encoding="utf-8")

    assert "for _ in 1 2 3 4 5 6" in validate
    assert "registration_ready" in validate
    assert "\"scenario\"[[:space:]]*:[[:space:]]*\"5g-sa\"" in validate
    assert 'find "$repo_dir/runs"' not in validate


@pytest.mark.parametrize(
    ("scenario", "script_path"),
    (
        ("4g-lte-sim", "deployments/4g-lte-sim/scripts/stop.sh"),
        ("5g-sa", "deployments/5g-sa/scripts/stop.sh"),
    ),
)
def test_simulation_stop_closes_only_its_latest_run(tmp_path: Path, scenario: str, script_path: str):
    project = tmp_path / "project"
    target_run = project / "runs/run-001"
    other_run = project / "runs/run-999"
    target_run.mkdir(parents=True)
    other_run.mkdir(parents=True)
    target_metadata = {
        "run_id": "run-001",
        "scenario": scenario,
        "finished_at": "",
        "status": "started",
    }
    other_metadata = {
        "run_id": "run-999",
        "scenario": "5g-sa" if scenario == "4g-lte-sim" else "4g-lte-sim",
        "finished_at": "",
        "status": "started",
    }
    (target_run / "metadata.json").write_text(json.dumps(target_metadata), encoding="utf-8")
    (other_run / "metadata.json").write_text(json.dumps(other_metadata), encoding="utf-8")
    source = ROOT / script_path
    copied_script = project / script_path
    copied_script.parent.mkdir(parents=True)
    copied_script.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    copied_script.chmod(0o755)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    docker.chmod(0o755)

    result = subprocess.run(
        [str(copied_script)],
        cwd=project,
        env={**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}"},
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    closed = json.loads((target_run / "metadata.json").read_text(encoding="utf-8"))
    untouched = json.loads((other_run / "metadata.json").read_text(encoding="utf-8"))
    assert closed["status"] == "stopped"
    assert closed["finished_at"]
    assert untouched == other_metadata
