from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DEPLOY = ROOT / "deployments" / "5g-nsa-x310"


def test_nsa_scenario_is_integrated_and_dual_channel():
    required = [
        DEPLOY / "docker-compose.yml",
        DEPLOY / ".env.example",
        DEPLOY / "ran" / "enb.conf",
        DEPLOY / "ran" / "rr.conf",
        DEPLOY / "ran" / "rb.conf",
        DEPLOY / "ran" / "sib.conf",
        DEPLOY / "rf" / "channel-plan.example.yaml",
        DEPLOY / "rf" / "safety-manifest.example.yaml",
        DEPLOY / "scripts" / "preflight.sh",
        DEPLOY / "scripts" / "validate.sh",
        DEPLOY / "scripts" / "start-rf.sh",
        DEPLOY / "scripts" / "emergency-stop.sh",
    ]
    assert [str(path) for path in required if not path.exists()] == []
    rr = (DEPLOY / "ran" / "rr.conf").read_text(encoding="utf-8")
    assert "rf_port = 0" in rr
    assert "rf_port = 1" in rr
    assert "dl_earfcn = 3150" in rr
    assert "dl_arfcn = 368500" in rr
    assert "band = 3" in rr
    rb = (DEPLOY / "ran" / "rb.conf").read_text(encoding="utf-8")
    assert "qci = 5" in rb
    assert "qci = 7" in rb
    assert "qci = 9" in rb
    assert "max_retx_thresh = 8" in rb
    enb = (DEPLOY / "ran" / "enb.conf").read_text(encoding="utf-8")
    assert "n_prb = 50" in enb
    assert "tx_gain = 20" in enb
    assert "rx_gain = 31.5" in enb
    assert "nof_phy_threads = 3" in enb
    assert "all_level = warning" in enb
    assert "rrc_level = info" in enb
    assert "pdsch_max_mcs = 6" in enb
    assert "pusch_max_mcs = 4" in enb
    assert "nr_pdsch_mcs = 4" in enb
    assert "nr_pusch_mcs = 4" in enb
    assert "send_frame_size=1472" in enb
    assert "recv_frame_size=1472" in enb
    rr = (DEPLOY / "ran" / "rr.conf").read_text(encoding="utf-8")
    assert "max_harq_tx = 8" in rr
    sib = (DEPLOY / "ran" / "sib.conf").read_text(encoding="utf-8")
    assert "max_harq_msg3_tx = 8" in sib
    assert "t301 = 1000" in sib
    assert "t310 = 1000" in sib
    assert "n310 = 6" in sib


def test_nsa_rf_is_blocked_and_time_limited():
    compose = (DEPLOY / "docker-compose.yml").read_text(encoding="utf-8")
    start = (DEPLOY / "scripts" / "start-rf.sh").read_text(encoding="utf-8")
    validate = (DEPLOY / "scripts" / "validate.sh").read_text(encoding="utf-8")
    preflight = (DEPLOY / "scripts" / "preflight.sh").read_text(encoding="utf-8")
    manifest = (DEPLOY / "rf" / "safety-manifest.example.yaml").read_text(encoding="utf-8")
    assert 'profiles: ["rf"]' in compose
    assert "timeout --signal=TERM" in compose
    assert "LAIN5G_ALLOW_5G_NSA_RF_START" in start
    assert "REQUIRE_RF_READY=true" in start
    assert "sleep 5" in start
    assert ".State.Running" in start
    assert "session_status=auto_stopped" in start
    assert '"scenario":"5g-nsa-x310"' in validate
    assert "nr_secondary_cell" in validate
    assert 'docker logs --timestamps --since "$session_started"' in validate
    assert "eNB-S1 accepted|Number of eNBs is now 1" in validate
    assert "cc_idx=1 nof_prb=" in validate
    assert "not confirmed on RF port 1" in validate
    assert "rfnoc_initialization FAIL" in validate
    assert "UHD could not initialize the RFNoC graph" in validate
    assert 'overall=PARTIAL' in validate
    assert "nr_rf_path_connected" in preflight
    assert "authorization_confirmed: false" in manifest
    assert "nr_rf_path_connected: false" in manifest
    assert "auto_stop: true" in manifest


def test_nsa_profile_and_preflight_use_effective_values():
    assert (ROOT / "config/profiles/5g-nsa-x310.yaml").is_file()
    preflight = (DEPLOY / "scripts/preflight.sh").read_text(encoding="utf-8")
    hardware = (DEPLOY / "scripts/hardware-check.sh").read_text(encoding="utf-8")
    assert 'field lte_dl_earfcn "$channel"' in preflight
    assert 'field nr_dl_arfcn "$channel"' in preflight
    assert '"$scenario_dir/.env"' in hardware
    assert "srsran4g-uhd:local" in hardware
    stop = (DEPLOY / "scripts" / "stop.sh").read_text(encoding="utf-8")
    core = (DEPLOY / "scripts" / "start-core.sh").read_text(encoding="utf-8")
    assert ".nsa-core-owned" in core
    assert ".nsa-core-owned" in stop
    assert "enb-x310" in stop


def test_nsa_deployment_is_public_and_reports_shared_core_services():
    registry = (ROOT / "src/backend/app/services/deployment_registry.py").read_text(encoding="utf-8")
    images = (ROOT / "src/backend/app/services/image_catalog.py").read_text(encoding="utf-8")
    assert '"5g-nsa-x310": DeploymentDefinition(' in registry
    assert '"rfnoc_initialization"' in registry[registry.index('"5g-nsa-x310": DeploymentDefinition('):registry.index('\n    ),', registry.index('"5g-nsa-x310": DeploymentDefinition('))]
    assert 'catalog_visible=False' not in registry[registry.index('"5g-nsa-x310": DeploymentDefinition('):registry.index('\n    ),', registry.index('"5g-nsa-x310": DeploymentDefinition('))]
    assert '"5g-nsa-x310")' in images


def test_nsa_rf_start_surfaces_rfnoc_diagnosis():
    service = (ROOT / "src/backend/app/services/deployment_service.py").read_text(encoding="utf-8")
    start = (DEPLOY / "scripts" / "start-rf.sh").read_text(encoding="utf-8")
    assert '"X310_RFNOC_INIT_FAILED"' in service
    assert "could not initialize its UHD/RFNoC radio graph" in service
    assert "Management operation failed" in start
    assert "Incorrect number of operations" in start
