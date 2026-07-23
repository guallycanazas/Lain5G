from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.dependencies import get_profile_config_service, settings_dependency
from backend.app.main import create_app
from backend.app.services.profile_config_service import ProfileConfigError, ProfileConfigService
from backend.app.settings import Settings

ROOT = Path(__file__).resolve().parents[2]


def make_profile_project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    shutil.copytree(ROOT / "config", root / "config")
    for rel in [
        "deployments/5g-sa/open5gs",
        "deployments/5g-sa/ueransim",
        "deployments/5g-vonr/open5gs",
        "deployments/5g-vonr/ueransim",
        "deployments/4g-volte/common/open5gs",
        "deployments/4g-volte/common/provisioning",
        "deployments/4g-volte/sim/ran",
        "deployments/4g-lte-sim/open5gs",
        "deployments/4g-lte-sim/ran",
        "deployments/4g-volte/x310/open5gs",
        "deployments/4g-volte/x310/ran",
        "deployments/4g-volte/x310/rf",
        "deployments/5g-sa-x310/open5gs",
        "deployments/5g-sa-x310/rf",
        "deployments/5g-nsa-x310",
    ]:
        shutil.copytree(ROOT / rel, root / rel)
    for scenario in ("deployments/4g-volte/x310", "deployments/5g-sa-x310", "deployments/5g-nsa-x310"):
        for name in ("channel-plan", "safety-manifest"):
            shutil.copyfile(root / scenario / "rf" / f"{name}.example.yaml", root / scenario / "rf" / f"{name}.yaml")
    channel_4g = root / "deployments/4g-volte/x310/rf/channel-plan.yaml"
    channel_4g.write_text(
        channel_4g.read_text(encoding="utf-8")
        .replace("downlink_frequency_hz:", "downlink_frequency_hz: 2660000000")
        .replace("uplink_frequency_hz:", "uplink_frequency_hz: 2540000000")
        .replace("tx_gain:", "tx_gain: 20"),
        encoding="utf-8",
    )
    channel_5g = root / "deployments/5g-sa-x310/rf/channel-plan.yaml"
    channel_5g.write_text(
        channel_5g.read_text(encoding="utf-8").replace("duplex_mode:", "duplex_mode: TDD"),
        encoding="utf-8",
    )
    profile_4g = root / "config/profiles/4g-lte-x310.yaml"
    profile_4g.write_text(
        profile_4g.read_text(encoding="utf-8")
        .replace("maximum_duration_seconds: 600", "maximum_duration_seconds: 60")
        .replace("environment: shielded", "environment: cabled")
        .replace("antenna_connected: true", "antenna_connected: false")
        .replace("shielded_environment: true", "shielded_environment: false")
        .replace("authorization_confirmed: true", "authorization_confirmed: false")
        .replace('operator_note: "Prueba RF autorizada en entorno blindado con antena conectada, atenuación 60 dB y auto-stop 600 s"', 'operator_note: ""')
        .replace("operator_note: Prueba RF autorizada en entorno blindado con antena conectada, atenuación 60 dB y auto-stop 600 s", 'operator_note: ""'),
        encoding="utf-8",
    )
    profile_5g = root / "config/profiles/5g-sa-x310.yaml"
    profile_5g.write_text(
        profile_5g.read_text(encoding="utf-8")
        .replace("band: 78", "band: null")
        .replace("band: 41", "band: null")
        .replace("dl_arfcn: 632628", "dl_arfcn: null")
        .replace("dl_arfcn: 520002", "dl_arfcn: null")
        .replace("authorization_confirmed: true", "authorization_confirmed: false"),
        encoding="utf-8",
    )
    (root / "deployments/5g-sa/.env").write_text("SUBSCRIBER_KEY=SECRETKEY\nSUBSCRIBER_OPC=SECRETOPC\nSUBSCRIBER_SQN=SECRETSEQ\n", encoding="utf-8")
    (root / "deployments/5g-vonr/.env").write_text("SUBSCRIBER_KEY=SECRETKEY\nSUBSCRIBER_OPC=SECRETOPC\nSUBSCRIBER_SQN=SECRETSEQ\nIMS_AUTH_PASSWORD=SECRETIMS\n", encoding="utf-8")
    (root / "deployments/4g-volte/common/.env").write_text("SUBSCRIBER_KEY=SECRETKEY\nSUBSCRIBER_OPC=SECRETOPC\nSUBSCRIBER_SQN=SECRETSEQ\nIMS_AUTH_PASSWORD=SECRETIMS\n", encoding="utf-8")
    (root / "deployments/5g-sa-x310/.env").write_text("", encoding="utf-8")
    return root


def service(root: Path) -> ProfileConfigService:
    return ProfileConfigService(Settings(project_root=root, dry_run=True))


def test_loads_profiles_and_blocks_invalid_rf_defaults(tmp_path: Path):
    svc = service(make_profile_project(tmp_path))
    profiles = svc.list_profiles()
    assert {item["profile"] for item in profiles} == {"4g-lte-sim", "4g-lte-x310", "5g-sa", "5g-sa-x310", "5g-nsa-x310"}
    validation = svc.validate_profile("5g-sa-x310")
    assert not validation["valid"]
    assert any("radio.band" in error for error in validation["errors"])
    assert any("radio.dl_arfcn" in error for error in validation["errors"])


def test_diff_apply_backup_and_secret_preservation(tmp_path: Path):
    root = make_profile_project(tmp_path)
    svc = service(root)
    tracked_before_update = snapshot_files(root)
    profile = svc.get_profile("5g-sa")
    profile["network"]["tac"] = 9
    profile["network"]["dnn"] = "labnet"
    profile["subscriber"]["imsi"] = "001010000000001"
    svc.update_profile("5g-sa", profile)
    tracked_before_apply = snapshot_files(root)
    diff = svc.diff_profile("5g-sa")
    assert any(file["changed"] for file in diff["files"])
    assert "SECRETKEY" not in "".join(file["diff"] for file in diff["files"])
    assert "SECRETOPC" not in "".join(file["diff"] for file in diff["files"])
    result = svc.apply_profile("5g-sa")
    assert result["backup"].startswith(".backups/config/5g-sa/")
    assert sorted(result["modified_files"]) == sorted(file["path"] for file in diff["files"] if file["changed"])
    env = (root / "deployments/5g-sa/.env").read_text(encoding="utf-8")
    assert "SUBSCRIBER_KEY=SECRETKEY" in env
    assert "SUBSCRIBER_OPC=SECRETOPC" in env
    assert "SUBSCRIBER_SQN=SECRETSEQ" in env
    assert "SUBSCRIBER_IMSI=001010000000001" in env
    assert "tac: 9" in (root / "deployments/5g-sa/open5gs/amf.yaml").read_text(encoding="utf-8")
    assert (root / result["backup"] / "deployments/5g-sa/.env").exists()
    changed_after_apply = changed_paths(tracked_before_apply, snapshot_files(root))
    assert changed_after_apply == set(result["modified_files"])
    assert not any(file["changed"] for file in svc.diff_profile("5g-sa")["files"])
    restore = svc.restore_profile("5g-sa")
    assert sorted(restore["restored_files"]) == sorted(result["modified_files"])
    restored_snapshot = snapshot_files(root)
    for path, content in tracked_before_update.items():
        if path.startswith("config/profiles/5g-sa.yaml"):
            continue
        assert restored_snapshot[path] == content


def test_vonr_apply_preserves_ims_and_subscriber_secrets_when_fields_are_absent(tmp_path: Path):
    root = make_profile_project(tmp_path)
    svc = service(root)
    profile = svc.get_profile("5g-vonr")
    profile["subscriber"]["imsi"] = "001010000000002"
    svc.update_profile("5g-vonr", profile)
    result = svc.apply_profile("5g-vonr")
    env = (root / "deployments/5g-vonr/.env").read_text(encoding="utf-8")
    assert "SUBSCRIBER_KEY=SECRETKEY" in env
    assert "SUBSCRIBER_OPC=SECRETOPC" in env
    assert "SUBSCRIBER_SQN=SECRETSEQ" in env
    assert "IMS_AUTH_PASSWORD=SECRETIMS" in env
    assert "SUBSCRIBER_IMSI=001010000000002" in env
    assert result["modified_files"]


def test_4g_lte_sim_profile_updates_only_epc_and_zmq_files(tmp_path: Path):
    root = make_profile_project(tmp_path)
    svc = service(root)
    profile = svc.get_profile("4g-lte-sim")
    assert svc.validate_profile("4g-lte-sim")["valid"] is True
    profile["network"]["tac"] = 8
    profile["network"]["apn_internet"] = "labnet"
    profile["ran"]["dl_earfcn"] = 3400
    profile["subscriber"]["imsi"] = "001010000000003"
    svc.update_profile("4g-lte-sim", profile)
    result = svc.apply_profile("4g-lte-sim")
    assert set(result["modified_files"]) == {
        "deployments/4g-volte/common/.env",
        "deployments/4g-lte-sim/open5gs/mme.yaml",
        "deployments/4g-lte-sim/open5gs/pgwc.yaml",
        "deployments/4g-lte-sim/ran/enb.conf",
        "deployments/4g-lte-sim/ran/ue.conf",
    }
    env = (root / "deployments/4g-volte/common/.env").read_text(encoding="utf-8")
    assert "SUBSCRIBER_KEY=SECRETKEY" in env
    assert "SUBSCRIBER_OPC=SECRETOPC" in env
    assert "APN_INTERNET=labnet" in env
    assert "dnn: labnet" in (root / "deployments/4g-lte-sim/open5gs/pgwc.yaml").read_text(encoding="utf-8")
    assert "dl_earfcn = 3400" in (root / "deployments/4g-lte-sim/ran/ue.conf").read_text(encoding="utf-8")


def test_api_uses_profile_service_without_file_paths(tmp_path: Path):
    svc = service(make_profile_project(tmp_path))
    app = create_app()
    app.dependency_overrides[get_profile_config_service] = lambda: svc
    app.dependency_overrides[settings_dependency] = lambda: Settings(
        project_root=svc.root,
        mutating_operations_enabled=True,
    )
    with TestClient(app) as client:
        assert client.get("/api/profiles").status_code == 200
        response = client.put("/api/profiles/5g-sa", json={"network": {"tac": 2}, "file": "/etc/passwd"})
        assert response.status_code == 422
        response = client.put("/api/profiles/5g-sa", json={"network": {"tac": 2}})
        assert response.status_code == 200
        assert client.post("/api/profiles/5g-sa/validate").json()["valid"] is True
        assert client.get("/api/profiles/5g-sa/diff").status_code == 200
        response = client.put("/api/profiles/5g-sa", json={"network": {"dnn": "internet\nMALICIOUS=value"}})
        assert response.status_code == 422
        assert response.json()["detail"]["code"] == "PROFILE_VALIDATION_FAILED"
    app.dependency_overrides.clear()


def test_cli_profile_commands_use_temporary_project(tmp_path: Path):
    root = make_profile_project(tmp_path)
    env = {**os.environ, "LAIN5G_PROJECT_ROOT": str(root)}
    list_result = subprocess.run([str(ROOT / "lain5g"), "profile", "list"], cwd=ROOT, env=env, text=True, capture_output=True, check=False)
    assert list_result.returncode == 0
    assert "5g-sa" in list_result.stdout
    validate_result = subprocess.run([str(ROOT / "lain5g"), "profile", "validate", "5g-sa-x310"], cwd=ROOT, env=env, text=True, capture_output=True, check=False)
    assert validate_result.returncode == 1
    assert "radio.band" in validate_result.stdout
    configure_result = subprocess.run(
        [str(ROOT / "lain5g"), "profile", "configure", "4g-lte-x310"],
        cwd=ROOT,
        env=env,
        input="\n" * 30,
        text=True,
        capture_output=True,
        check=False,
    )
    assert configure_result.returncode == 0
    for prompt in [
        "Channel bandwidth MHz [5]:",
        "Laboratory mode [cabled]:",
        "Attenuation dB [60]:",
        "Antenna connected [no]:",
        "Shielded environment [no]:",
        "Auto-stop enabled [yes]:",
        "RF authorization confirmed [no]:",
        "Authorization note []:",
        "Maximum duration seconds [60]:",
    ]:
        assert prompt in configure_result.stdout


def test_cli_guided_wizard_and_decimal_nsa_gain(tmp_path: Path):
    root = make_profile_project(tmp_path)
    env = {**os.environ, "LAIN5G_PROJECT_ROOT": str(root)}
    wizard = subprocess.run(
        [str(ROOT / "lain5g"), "profile", "wizard", "4g-lte-sim"],
        cwd=ROOT,
        env=env,
        input="5\n" + "\n" * 8 + "n\n\n0\n",
        text=True,
        capture_output=True,
        check=False,
    )
    assert wizard.returncode == 0
    assert "CONFIGURADOR DEL LABORATORIO LAIN" in wizard.stdout
    assert "[1. Red movil]" in wizard.stdout
    assert "[3. Acceso de radio]" in wizard.stdout
    assert "No se guardaron cambios." in wizard.stdout

    console = subprocess.run(
        [str(ROOT / "lain5g"), "profile", "wizard", "4g-lte-sim"],
        cwd=ROOT,
        env=env,
        input="0\n",
        text=True,
        capture_output=True,
        check=False,
    )
    assert console.returncode == 0
    assert "CONSOLA OPERATIVA LAIN" in console.stdout
    assert "[1] Iniciar simulacion" in console.stdout
    assert "[3] Validar" in console.stdout
    assert "[4] Logs recientes" in console.stdout
    assert "[6] Detener" in console.stdout

    values = [""] * 15 + ["30.5"] + [""] * 13
    configure = subprocess.run(
        [str(ROOT / "lain5g"), "profile", "configure", "5g-nsa-x310"],
        cwd=ROOT,
        env=env,
        input="\n".join(values) + "\n",
        text=True,
        capture_output=True,
        check=False,
    )
    assert configure.returncode == 0
    assert "[4. Dispositivo y senal RF]" in configure.stdout
    assert service(root).get_profile("5g-nsa-x310")["radio"]["rx_gain"] == 30.5


def test_4g_lte_x310_rf_safety_validation_and_apply_restore(tmp_path: Path):
    root = make_profile_project(tmp_path)
    svc = service(root)
    profile = svc.get_profile("4g-lte-x310")
    assert profile["safety"]["authorization_confirmed"] is False
    validation = svc.validate_profile("4g-lte-x310")
    assert not validation["valid"]
    assert any("authorization" in error for error in validation["errors"])
    with pytest.raises(ProfileConfigError):
        svc.apply_profile("4g-lte-x310")

    profile["safety"]["authorization_confirmed"] = True
    profile["safety"]["operator_note"] = "Cabled X310 test with 60 dB attenuation."
    profile["safety"]["auto_stop"] = False
    svc.update_profile("4g-lte-x310", profile)
    validation = svc.validate_profile("4g-lte-x310")
    assert not validation["valid"]
    assert any("auto_stop=true" in error for error in validation["errors"])

    profile["safety"]["auto_stop"] = True
    profile["safety"]["operator_note"] = ""
    svc.update_profile("4g-lte-x310", profile)
    validation = svc.validate_profile("4g-lte-x310")
    assert not validation["valid"]
    assert any("operator_note" in error for error in validation["errors"])

    profile["safety"]["operator_note"] = "Cabled X310 test with 60 dB attenuation."
    profile["radio"]["lte_band"] = 7
    profile["radio"]["earfcn"] = 3150
    profile["radio"]["bandwidth_mhz"] = 5
    profile["radio"]["tx_gain"] = 20
    profile["radio"]["rx_gain"] = 30
    svc.update_profile("4g-lte-x310", profile)
    validation = svc.validate_profile("4g-lte-x310")
    assert validation == {"profile": "4g-lte-x310", "valid": True, "errors": []}

    enb_path = root / "deployments/4g-volte/x310/ran/enb.conf"
    enb_path.write_text(enb_path.read_text(encoding="utf-8").replace("n_prb = 25", "n_prb = 50"), encoding="utf-8")
    channel_path = root / "deployments/4g-volte/x310/rf/channel-plan.yaml"
    channel_path.write_text(channel_path.read_text(encoding="utf-8").replace("tx_gain: 20", "tx_gain: 0"), encoding="utf-8")
    tracked_before_apply = snapshot_files(root)

    diff = svc.diff_profile("4g-lte-x310")
    assert [file["path"] for file in diff["files"]] == [
        "deployments/4g-volte/common/.env",
        "deployments/4g-volte/x310/open5gs/mme.yaml",
        "deployments/4g-volte/x310/open5gs/pgwc.yaml",
        "deployments/4g-volte/x310/ran/enb.conf",
        "deployments/4g-volte/x310/rf/channel-plan.yaml",
        "deployments/4g-volte/x310/rf/safety-manifest.yaml",
    ]
    result = svc.apply_profile("4g-lte-x310")
    expected = {
        "deployments/4g-volte/common/.env",
        "deployments/4g-volte/x310/open5gs/mme.yaml",
        "deployments/4g-volte/x310/ran/enb.conf",
        "deployments/4g-volte/x310/rf/channel-plan.yaml",
        "deployments/4g-volte/x310/rf/safety-manifest.yaml",
    }
    assert set(result["modified_files"]) == expected
    assert "n_prb = 25" in enb_path.read_text(encoding="utf-8")
    assert "downlink_frequency_hz: 2660000000" in channel_path.read_text(encoding="utf-8")
    assert "authorization_confirmed: true" in (root / "deployments/4g-volte/x310/rf/safety-manifest.yaml").read_text(encoding="utf-8")
    assert (root / result["backup"] / "deployments/4g-volte/x310/ran/enb.conf").exists()
    assert changed_paths(tracked_before_apply, snapshot_files(root)) == expected

    restore = svc.restore_profile("4g-lte-x310")
    assert set(restore["restored_files"]) == expected | {"deployments/4g-volte/x310/open5gs/mme.yaml", "deployments/4g-volte/x310/open5gs/pgwc.yaml"}
    restored_snapshot = snapshot_files(root)
    for path, content in tracked_before_apply.items():
        if path.startswith("config/profiles/4g-lte-x310.yaml"):
            continue
        assert restored_snapshot[path] == content


def test_5g_x310_apply_updates_effective_core_radio_and_safety_files(tmp_path: Path):
    root = make_profile_project(tmp_path)
    svc = service(root)
    profile = svc.get_profile("5g-sa-x310")
    profile["network"]["tac"] = 9
    profile["network"]["dnn"] = "x310net"
    profile["radio"].update({"band": 78, "dl_arfcn": 632700, "bandwidth_mhz": 20, "tx_gain": 22, "rx_gain": 31})
    profile["safety"]["authorization_confirmed"] = True
    profile["safety"]["operator_note"] = "Authorized shielded 5G X310 test."
    profile["safety"]["maximum_duration_seconds"] = 120
    svc.update_profile("5g-sa-x310", profile)
    assert svc.validate_profile("5g-sa-x310") == {"profile": "5g-sa-x310", "valid": True, "errors": []}

    result = svc.apply_profile("5g-sa-x310")
    assert set(result["modified_files"]) == {
        "deployments/5g-sa-x310/.env",
        "deployments/5g-sa-x310/open5gs/amf.yaml",
        "deployments/5g-sa-x310/open5gs/smf.yaml",
        "deployments/5g-sa-x310/rf/channel-plan.yaml",
        "deployments/5g-sa-x310/rf/safety-manifest.yaml",
    }
    assert "TAC=9" in (root / "deployments/5g-sa-x310/.env").read_text(encoding="utf-8")
    assert "SAMPLE_RATE_MHZ=23.04" in (root / "deployments/5g-sa-x310/.env").read_text(encoding="utf-8")
    assert "tac: 9" in (root / "deployments/5g-sa-x310/open5gs/amf.yaml").read_text(encoding="utf-8")
    assert "dnn: x310net" in (root / "deployments/5g-sa-x310/open5gs/smf.yaml").read_text(encoding="utf-8")
    channel = (root / "deployments/5g-sa-x310/rf/channel-plan.yaml").read_text(encoding="utf-8")
    assert "dl_arfcn: 632700" in channel
    assert "duplex_mode: TDD" in channel
    assert "authorized_lab_frequency: true" in channel
    safety = (root / "deployments/5g-sa-x310/rf/safety-manifest.yaml").read_text(encoding="utf-8")
    assert "maximum_duration_seconds: 120" in safety
    assert "authorization_confirmed: true" in safety


def test_5g_nsa_x310_profile_updates_dual_rat_radio_and_safety(tmp_path: Path):
    root = make_profile_project(tmp_path)
    svc = service(root)
    assert svc.validate_profile("5g-nsa-x310")["valid"] is False

    profile = svc.get_profile("5g-nsa-x310")
    profile["network"].update({"tac": 8, "apn_internet": "nsa-lab"})
    profile["radio"].update({"earfcn": 3200, "nr_dl_arfcn": 369000, "tx_gain": 21, "rx_gain": 30.5})
    profile["safety"].update(
        {
            "maximum_duration_seconds": 300,
            "environment": "shielded",
            "shielded_environment": True,
            "authorization_confirmed": True,
            "nr_rf_path_connected": True,
            "authorized_lab_frequencies": True,
            "operator_note": "Authorized shielded NSA B7+n3 test.",
        }
    )
    svc.update_profile("5g-nsa-x310", profile)
    assert svc.validate_profile("5g-nsa-x310")["valid"] is True

    result = svc.apply_profile("5g-nsa-x310")
    assert set(result["modified_files"]) == {
        "deployments/4g-volte/common/.env",
        "deployments/4g-volte/x310/open5gs/mme.yaml",
        "deployments/4g-volte/x310/open5gs/pgwc.yaml",
        "deployments/5g-nsa-x310/.env",
        "deployments/5g-nsa-x310/ran/enb.conf",
        "deployments/5g-nsa-x310/ran/rr.conf",
        "deployments/5g-nsa-x310/rf/channel-plan.yaml",
        "deployments/5g-nsa-x310/rf/safety-manifest.yaml",
    }
    enb = (root / "deployments/5g-nsa-x310/ran/enb.conf").read_text(encoding="utf-8")
    assert "tx_gain = 21" in enb
    assert "rx_gain = 30.5" in enb
    rr = (root / "deployments/5g-nsa-x310/ran/rr.conf").read_text(encoding="utf-8")
    assert rr.count("tac = 0x0008") == 2
    assert "dl_earfcn = 3200;" in rr
    assert "dl_arfcn = 369000;" in rr
    channel = (root / "deployments/5g-nsa-x310/rf/channel-plan.yaml").read_text(encoding="utf-8")
    assert "lte_downlink_frequency_mhz: 2665.0" in channel
    assert "nr_downlink_frequency_mhz: 1845.0" in channel
    env = (root / "deployments/5g-nsa-x310/.env").read_text(encoding="utf-8")
    assert "RF_DURATION_SECONDS=300" in env
    assert "LAIN5G_ALLOW_5G_NSA_RF_START=false" in env


def test_5g_nsa_x310_rejects_unsupported_or_unsafe_values(tmp_path: Path):
    svc = service(make_profile_project(tmp_path))
    profile = svc.get_profile("5g-nsa-x310")
    profile["radio"].update({"bandwidth_mhz": 20, "nr_dl_arfcn": 369001, "rx_gain": -1})
    profile["safety"].update({"nr_rf_path_connected": False, "authorized_lab_frequencies": False})
    svc.update_profile("5g-nsa-x310", profile)
    errors = svc.validate_profile("5g-nsa-x310")["errors"]
    assert any("bandwidth_mhz must be 10" in error for error in errors)
    assert any("100 kHz raster" in error for error in errors)
    assert any("rx_gain" in error for error in errors)
    assert any("nr_rf_path_connected" in error for error in errors)
    assert any("authorized_lab_frequencies" in error for error in errors)


def test_no_rf_start_commands_in_profile_service():
    text = (ROOT / "backend/app/services/profile_config_service.py").read_text(encoding="utf-8")
    forbidden = ["docker compose up", "start-gnb", "start-enb", "uhd_image_loader", "docker system prune"]
    for item in forbidden:
        assert item not in text


def snapshot_files(root: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for path in root.rglob("*"):
        if not path.is_file() or ".backups" in path.parts:
            continue
        files[str(path.relative_to(root))] = path.read_text(encoding="utf-8")
    return files


def changed_paths(before: dict[str, str], after: dict[str, str]) -> set[str]:
    return {path for path, content in after.items() if before.get(path) != content}
