from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
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


def test_volte_sim_run_metadata_is_unique_and_closed_on_stop():
    start = (DEPLOY / "sim" / "scripts" / "start.sh").read_text(encoding="utf-8")
    stop = (DEPLOY / "sim" / "scripts" / "stop.sh").read_text(encoding="utf-8")

    assert 'run_id="run-$(date -u +%Y%m%d-%H%M%S)"' in start
    assert 'if mkdir "$run_dir" 2>/dev/null; then' in start
    assert '"git_commit":"$git_commit"' in start
    assert '"scenario"[[:space:]]*:[[:space:]]*"4g-volte-sim"' in stop
    assert 'metadata["finished_at"]' in stop
    assert 'metadata["status"] = "stopped"' in stop
    assert 'compose logs --no-color --tail 1000 > "$latest_run/logs/docker-compose.log"' in stop
    assert "compose stop" in stop
    assert "volume rm" not in stop
    assert "down -v" not in stop


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
    assert "sleep 10" in start_enb
    assert ".State.Running" in start_enb
    assert "--network host" in uhd_check
    assert "uhd_usrp_probe" in uhd_check
    assert uhd_check.index('if docker image inspect "$image"') < uhd_check.index('elif command -v uhd_usrp_probe')
    assert 'cmd=(docker run --rm --network host "$image" uhd_usrp_probe' in uhd_check
    assert "for attempt in 1 2 3" in uhd_check
    assert "probe failed after 3 attempts" in uhd_check
    assert "uhd_find_devices" in hardware_check
    assert 'ip -4 route get "$addr"' in hardware_check
    assert 'route_source="$(awk' in hardware_check
    assert 'check ethernet_link PASS "route to $addr uses $route_device at $route_source"' in hardware_check


def test_x310_validation_uses_session_scoped_logs_and_marks_idle_standby():
    validate = (DEPLOY / "x310" / "scripts" / "validate.sh").read_text(encoding="utf-8")

    host_hardware_check = (DEPLOY / "x310" / "scripts" / "host-hardware-check.sh").read_text(encoding="utf-8")
    preflight = (DEPLOY / "x310" / "scripts" / "preflight.sh").read_text(encoding="utf-8")

    assert 'docker run --rm --network host' in host_hardware_check
    assert 'host-hardware-check.sh' in validate
    assert 'host-hardware-check.sh' in preflight
    assert 'add enb_started NOT_TESTED "No active RF session' in validate
    assert 'add s1_setup NOT_TESTED "No active RF session' in validate
    assert 'add auto_stop NOT_TESTED "No current RF session lifecycle' in validate
    assert 'add enb_started PASS "RF session completed"' not in validate


def test_x310_rf_start_captures_failed_initialization_evidence():
    start_enb = (DEPLOY / "x310" / "scripts" / "start-enb.sh").read_text(encoding="utf-8")
    validate = (DEPLOY / "x310" / "scripts" / "validate.sh").read_text(encoding="utf-8")

    assert 'status":"failed"' in start_enb
    assert 'logs --no-color --since "$started_at" enb-x310' in start_enb
    assert 'tail -n 45 "$run_dir/logs/enb-x310.log"' in start_enb
    assert 'name rf-session.json' in validate
    assert 'Latest RF session failed during eNB startup' in validate
    assert 'S1 setup evidence found in session' in validate


def test_x310_uses_profile_specific_addresses():
    compose = (DEPLOY / "x310" / "docker-compose.yml").read_text(encoding="utf-8")
    enb = (DEPLOY / "x310" / "ran" / "enb.conf").read_text(encoding="utf-8")
    assert "./open5gs/mme.yaml" in compose
    assert "./ims/pcscf/kamailio.cfg" in compose
    assert "gateway: 10.42.0.1" in compose
    assert "mme_addr = 10.42.0.10" in enb
    assert "s1c_bind_addr = 10.42.0.1" in enb
    assert "gtp_bind_addr = 10.42.0.1" in enb
    for path in (DEPLOY / "x310" / "open5gs").glob("*.yaml"):
        text = path.read_text(encoding="utf-8")
        assert "10.41." not in text


def test_x310_supports_ims_signaling_bearer():
    rb = (DEPLOY / "x310" / "ran" / "rb.conf").read_text(encoding="utf-8")
    assert "qci = 5;" in rb


def test_x310_compact_ims_is_always_started():
    compose = (DEPLOY / "x310" / "docker-compose.yml").read_text(encoding="utf-8")
    start = (DEPLOY / "x310" / "scripts" / "start-epc.sh").read_text(encoding="utf-8")
    validate = (DEPLOY / "x310" / "scripts" / "validate.sh").read_text(encoding="utf-8")

    assert "ims-internal" not in compose
    for service in ("ims-database", "ims-provisioner", "pcscf", "icscf", "scscf", "dns"):
        assert f"  {service}:" in compose
    assert "service_healthy" in compose
    assert "EPC + IMS" in start
    assert "ims_services PASS" in validate


def test_x310_rf_profile_does_not_include_virtual_phones_or_call_check():
    compose = (DEPLOY / "x310" / "docker-compose.yml").read_text(encoding="utf-8")
    validate = (DEPLOY / "x310" / "scripts/validate.sh").read_text(encoding="utf-8")
    simulation = (DEPLOY / "sim" / "docker-compose.yml").read_text(encoding="utf-8")
    scscf = (ROOT / "images" / "ims-sip" / "scscf_server.py").read_text(encoding="utf-8")
    registry = (ROOT / "src/backend/app/services/deployment_registry.py").read_text(encoding="utf-8")

    assert "virtual-phones:" not in compose
    assert "VIRTUAL_PHONE_" not in compose
    assert "validate-ims-virtual-call.sh" not in validate
    assert "virtual_call" not in validate
    assert 'os.environ.get(f"VIRTUAL_PHONE_{label}_NUMBER", "")' in scscf
    assert 'os.environ.get(f"VIRTUAL_PHONE_{label}_PASSWORD", "")' in scscf
    assert '"virtual-phone-a-lab-only"' not in scscf
    assert "virtual-phones:" in simulation
    assert "VIRTUAL_PHONE_A_NUMBER" in simulation
    assert 'id="4g-lte-x310"' in registry
    rf_definition = registry.split('id="4g-lte-x310"', 1)[1].split('id="5g-sa-x310"', 1)[0]
    assert "virtual_call" not in rf_definition


def test_secret_values_are_not_committed_in_env_example():
    env = (DEPLOY / "common" / ".env.example").read_text(encoding="utf-8")
    assert "SUBSCRIBER_KEY=\n" in env
    assert "SUBSCRIBER_OPC=\n" in env
    assert "IMS_AUTH_PASSWORD=\n" in env
