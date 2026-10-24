import json
import subprocess

import pytest

from backend.app.models.real_ims import RealIMSSubscriber, RealIMSSubscriberList, RealIMSSubscriberSummary
from backend.app.services.real_ims_service import PYHSS_REQUEST_HELPER, RealIMSError, RealIMSService, _last_integer, _open5gs_document
from backend.app.settings import Settings


def make_service(tmp_path):
    root = tmp_path / "project"
    stack = root / "deployments" / "ims-real"
    stack.mkdir(parents=True)
    return RealIMSService(Settings(project_root=root, command_timeout=1))


def subscriber():
    return RealIMSSubscriber(
        imsi="001010000000001",
        msisdn="15551234567",
        ki="00112233445566778899AABBCCDDEEFF",
        opc="FFEEDDCCBBAA99887766554433221100",
    )


def test_open5gs_document_contains_internet_and_ims_voice_policy():
    document = _open5gs_document(subscriber())
    sessions = document["slice"][0]["session"]

    assert [item["name"] for item in sessions] == ["internet", "ims"]
    assert sessions[0]["qos"]["index"] == 9
    assert sessions[0]["qos"]["arp"]["priority_level"] == 8
    assert sessions[0]["pcc_rule"] == []
    assert sessions[1]["qos"]["index"] == 5
    assert sessions[1]["qos"]["arp"]["priority_level"] == 1
    assert [rule["qos"]["index"] for rule in sessions[1]["pcc_rule"]] == [1, 2]


def test_sync_subscriber_copies_local_authentication_data_without_returning_secrets(tmp_path, monkeypatch):
    service = make_service(tmp_path)
    source_env = service._state_dir("4g") / "stack.env"
    target_env = service._state_dir("5g") / "stack.env"
    source_env.parent.mkdir(parents=True)
    target_env.parent.mkdir(parents=True)
    source_env.write_text("MCC=001\nMNC=01\n", encoding="utf-8")
    target_env.write_text("MCC=001\nMNC=01\n", encoding="utf-8")
    (target_env.parent / "override.yaml").write_text("services: {}\n", encoding="utf-8")
    service._state_dir("5g").mkdir(parents=True, exist_ok=True)
    service._write_json = lambda *_: None
    service.subscribers = lambda mode: RealIMSSubscriberList(
        mode=mode,
        count=1,
        subscribers=[RealIMSSubscriberSummary(
            imsi="001010000000001", msisdn="15551234567", impi="impi", impu="impu", domain="ims.example",
            enabled=True, apns=["internet", "ims"], open5gs_present=True, pyhss_present=True,
        )],
    )
    secret_ki = "00112233445566778899AABBCCDDEEFF"
    secret_opc = "FFEEDDCCBBAA99887766554433221100"
    monkeypatch.setattr(service, "_run", lambda *args, **kwargs: subprocess.CompletedProcess(
        [], 0, json.dumps({"imsi": "001010000000001", "msisdn": ["15551234567"], "security": {
            "k": secret_ki, "opc": secret_opc, "amf": "8000", "sqn": "00000000000A",
        }, "subscriber_status": 0}), "",
    ))
    captured = {}

    def fake_provision(mode, current, mcc, mnc, *, execute):
        captured.update(mode=mode, subscriber=current, mcc=mcc, mnc=mnc, execute=execute)
        return {"mode": mode, "status": "PASS", "imsi": current.imsi}

    monkeypatch.setattr(service, "provision", fake_provision)
    result = service.sync_subscriber("4g", "5g", "001010000000001")

    assert captured["mode"] == "5g"
    assert captured["execute"] is True
    assert captured["subscriber"].ki == secret_ki
    assert captured["subscriber"].opc == secret_opc
    assert captured["subscriber"].sqn == 10
    assert result["status"] == "PASS"
    assert result["secrets_redacted"] is True
    assert secret_ki not in json.dumps(result)
    assert secret_opc not in json.dumps(result)


def test_last_integer_accepts_mongosh_prompt():
    assert _last_integer("open5gs> 1\n\nopen5gs> ") == 1


def test_registration_check_accepts_kamailio_ims_auth_evidence(tmp_path, monkeypatch):
    service = make_service(tmp_path)
    logs = """
PCSCF: REGISTER sip:ims.mnc001.mcc001.3gppnetwork.org
MAR success - 401/407 response sent from module
ims_authenticate(): vector 0x123 successfully used 1 time(s)
SAR success - 200 response sent from module
"""
    monkeypatch.setattr(service, "_run", lambda *args, **kwargs: subprocess.CompletedProcess([], 0, logs, ""))

    check = service._registration_check("4g", service._state_dir("4g") / "stack.env")

    assert check.status == "PASS"


def test_compose_commands_are_namespaced_and_stop_keeps_volumes(tmp_path, monkeypatch):
    service = make_service(tmp_path)
    state = service._state_dir("4g")
    state.mkdir(parents=True)
    env_file = state / "stack.env"
    env_file.write_text("MCC=001\nMNC=01\n", encoding="utf-8")
    (state / "override.yaml").write_text("services: {}\n", encoding="utf-8")
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(service, "_run", fake_run)
    result = service.stop("4g", execute=True)

    command = calls[0]
    assert command[:5] == ["docker", "compose", "-p", "lain5g-lab-ims-real-4g", "--env-file"]
    assert "compose.4g.yaml" in " ".join(command)
    assert command[-1] == "down"
    assert "-v" not in command
    assert "--volumes" not in command
    assert result["volumes_deleted"] is False


def test_start_and_image_build_are_dry_run_by_default(tmp_path, monkeypatch):
    service = make_service(tmp_path)
    monkeypatch.setattr(service, "_run", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("executed")))

    start = service.start("5g")
    images = service.build_images()

    assert start["executed"] is False
    assert start["rf_started"] is False
    assert "lain5g-lab-ims-real-5g" in start["command"]
    assert images["executed"] is False


def test_start_uses_prepared_images_without_building(tmp_path, monkeypatch):
    service = make_service(tmp_path)
    calls = []

    class Report:
        checks = []

    env_file = service._state_dir("4g") / "stack.env"
    env_file.parent.mkdir(parents=True)
    env_file.write_text("MCC=001\nMNC=01\n", encoding="utf-8")
    monkeypatch.setattr(service, "preflight", lambda mode: Report())
    monkeypatch.setattr(service, "build_images", lambda **kwargs: (_ for _ in ()).throw(AssertionError("start must not build images")))
    monkeypatch.setattr(service, "_prepare_runtime", lambda *args, **kwargs: env_file)
    monkeypatch.setattr(service, "_compose_command", lambda *args: ["docker", "compose", "up"])
    monkeypatch.setattr(service, "_run", lambda command, **kwargs: calls.append(command) or subprocess.CompletedProcess(command, 0, "", ""))

    result = service.start("4g", execute=True)

    assert calls == [["docker", "compose", "up", "-d", *service._services("4g")]]
    assert result["status"] == "RUNNING"


def test_start_blocks_when_preflight_reports_missing_images(tmp_path, monkeypatch):
    service = make_service(tmp_path)

    class Check:
        status = "FAIL"
        message = "Prepare missing IMS images first"

    class Report:
        checks = [Check()]

    monkeypatch.setattr(service, "preflight", lambda mode: Report())
    monkeypatch.setattr(service, "build_images", lambda **kwargs: (_ for _ in ()).throw(AssertionError("start must not build images")))

    with pytest.raises(RealIMSError, match="Prepare missing IMS images first"):
        service.start("4g", execute=True)


def test_pyhss_request_uses_compose_exec_and_stdin_envelope(tmp_path, monkeypatch):
    service = make_service(tmp_path)
    state = service._state_dir("5g")
    state.mkdir(parents=True)
    env_file = state / "stack.env"
    env_file.write_text("MCC=001\nMNC=01\n", encoding="utf-8")
    (state / "override.yaml").write_text("services: {}\n", encoding="utf-8")
    (state / "provisioning.key").write_text("provisioning-secret\n", encoding="utf-8")
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["stdin"] = kwargs["input_text"]
        return subprocess.CompletedProcess(command, 0, "{}\n", "")

    monkeypatch.setattr(service, "_run", fake_run)
    service._pyhss_request("5g", env_file, "PATCH", "/auc/10", {"ki": subscriber().ki}, None)

    command = captured["command"]
    assert command[-5:] == ["-T", "pyhss", "python3", "-c", PYHSS_REQUEST_HELPER]
    assert "docker" == command[0] and "compose" == command[1]
    assert "provisioning-secret" not in command
    assert subscriber().ki not in command
    envelope = json.loads(captured["stdin"])
    assert envelope["key"] == "provisioning-secret"
    assert envelope["body"]["ki"] == subscriber().ki


def test_service_has_no_direct_host_pyhss_url(tmp_path):
    service = make_service(tmp_path)
    assert not hasattr(service, "pyhss_url")
    assert "127.0.0.1:8080" not in " ".join(service._compose_command("4g", service._state_dir("4g") / "stack.env", "exec"))


def test_subscriber_list_correlates_pyhss_and_open5gs_without_secrets(tmp_path, monkeypatch):
    service = make_service(tmp_path)
    state = service._state_dir("4g")
    state.mkdir(parents=True)
    (state / "stack.env").write_text("MCC=001\nMNC=01\n", encoding="utf-8")
    (state / "override.yaml").write_text("services: {}\n", encoding="utf-8")

    class FakePyHSS:
        def list_ims_subscribers(self):
            return [{"imsi": "001010000000001", "msisdn": "15551234567", "scscf_realm": "ims.mnc001.mcc001.3gppnetwork.org", "scscf": "sip:scscf:6060", "ki": subscriber().ki}]

        def list_packet_subscribers(self):
            return [{"imsi": "001010000000001", "enabled": True, "auc_id": 10}]

    monkeypatch.setattr(service, "_pyhss", lambda *args: FakePyHSS())
    monkeypatch.setattr(
        service,
        "_run",
        lambda command, **kwargs: subprocess.CompletedProcess(
            command,
            0,
            '[{"imsi":"001010000000001","msisdn":["15551234567"],"slice":[{"session":[{"name":"internet"},{"name":"ims"}]}]}]\n',
            "",
        ),
    )

    result = service.subscribers("4g")

    assert result.count == 1
    assert result.subscribers[0].apns == ["ims", "internet"]
    assert result.subscribers[0].open5gs_present is True
    serialized = result.model_dump_json()
    assert subscriber().ki not in serialized
    assert "auc_id" not in serialized


def test_rejects_non_allowlisted_real_ims_command_before_subprocess(tmp_path, monkeypatch):
    service = make_service(tmp_path)
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("executed")))

    with pytest.raises(RealIMSError, match="not allowlisted"):
        service._run(["sh", "-c", "id"])


def test_rejects_real_ims_compose_path_outside_project(tmp_path, monkeypatch):
    service = make_service(tmp_path)
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("executed")))

    with pytest.raises(RealIMSError, match="outside"):
        service._run(["docker", "compose", "-f", "/etc/passwd", "ps"])

    with pytest.raises(RealIMSError, match="outside"):
        service._run(["docker", "compose", "-f", "../../../compose.yaml", "ps"])


def test_rejects_non_allowlisted_real_ims_compose_action(tmp_path, monkeypatch):
    service = make_service(tmp_path)
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("executed")))

    with pytest.raises(RealIMSError, match="not allowlisted"):
        service._run(["docker", "compose", "config"])


def test_real_ims_subprocess_explicitly_disables_shell(tmp_path, monkeypatch):
    service = make_service(tmp_path)
    observed = {}

    def fake_run(command, **kwargs):
        observed["shell"] = kwargs.get("shell")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = service._run(["docker", "compose", "version"])

    assert result.returncode == 0
    assert observed["shell"] is False


def test_real_ims_timeout_is_controlled(tmp_path, monkeypatch):
    service = make_service(tmp_path)

    def timeout(command, **kwargs):
        raise subprocess.TimeoutExpired(command, 1)

    monkeypatch.setattr(subprocess, "run", timeout)
    result = service._run(["docker", "compose", "version"], check=False)

    assert result.returncode == 124
    assert result.stderr == "command timed out"
