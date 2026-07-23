from __future__ import annotations

import os
import re
import stat
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIRS = (
    Path("deployments/4g-volte/x310/scripts"),
    Path("deployments/5g-sa-x310/scripts"),
    Path("deployments/5g-nsa-x310/scripts"),
)
RF_SCRIPTS = tuple(
    script.relative_to(ROOT)
    for script_dir in SCRIPT_DIRS
    for script in sorted((ROOT / script_dir).glob("*.sh"))
)
CANARY = "SYNTHETIC_PRIVATE_RF_CANARY_DO_NOT_PRINT"
DANGEROUS_COMMANDS = (
    "awk",
    "cat",
    "cp",
    "cpupower",
    "date",
    "dd",
    "docker",
    "gnb",
    "grep",
    "head",
    "ip",
    "iptables",
    "kill",
    "mkdir",
    "mount",
    "mv",
    "nft",
    "ping",
    "pkill",
    "rm",
    "route",
    "sed",
    "sleep",
    "srsenb",
    "srsepc",
    "sudo",
    "tail",
    "tee",
    "timeout",
    "touch",
    "tr",
    "uhd_config_info",
    "uhd_find_devices",
    "uhd_image_loader",
    "uhd_usrp_probe",
    "umount",
)


def _snapshot(root: Path) -> dict[str, tuple[str, int, bytes]]:
    snapshot = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        mode = stat.S_IMODE(path.stat().st_mode)
        if path.is_file():
            snapshot[relative] = ("file", mode, path.read_bytes())
        else:
            snapshot[relative] = ("directory", mode, b"")
    return snapshot


@pytest.fixture
def rf_dry_run_sandbox(tmp_path: Path) -> tuple[Path, Path, dict[str, str]]:
    sandbox = tmp_path / "repo"
    sandbox_tmp = sandbox / "tmp"
    sandbox_tmp.mkdir(parents=True)

    for script_dir in SCRIPT_DIRS:
        destination = sandbox / script_dir
        destination.mkdir(parents=True)
        for source in (ROOT / script_dir).glob("*.sh"):
            target = destination / source.name
            text = source.read_text(encoding="utf-8").replace("/tmp/", f"{sandbox_tmp.as_posix()}/")
            target.write_text(text, encoding="utf-8")
            target.chmod(stat.S_IMODE(source.stat().st_mode))

    scenario_dirs = (
        sandbox / "deployments/4g-volte/x310",
        sandbox / "deployments/5g-sa-x310",
        sandbox / "deployments/5g-nsa-x310",
    )
    for scenario_dir in scenario_dirs:
        rf_dir = scenario_dir / "rf"
        rf_dir.mkdir(parents=True, exist_ok=True)
        (scenario_dir / ".env").write_text(f"PRIVATE_VALUE={CANARY}\n", encoding="utf-8")
        (scenario_dir / ".rf-active").write_text(f"marker={CANARY}\n", encoding="utf-8")
        (rf_dir / "channel-plan.yaml").write_text(f"private_channel: {CANARY}\n", encoding="utf-8")
        (rf_dir / "safety-manifest.yaml").write_text(f"operator_note: {CANARY}\n", encoding="utf-8")

    common_dir = sandbox / "deployments/4g-volte/common"
    common_dir.mkdir(parents=True)
    (common_dir / ".env").write_text(f"PRIVATE_VALUE={CANARY}\n", encoding="utf-8")
    runs_dir = sandbox / "runs"
    runs_dir.mkdir()
    (runs_dir / "existing-state").write_text(CANARY, encoding="utf-8")

    command_log = tmp_path / "external-command.log"
    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    stub = '#!/usr/bin/env bash\nprintf \'%s\\n\' "$0" >>"${LAIN5G_COMMAND_LOG:?}"\nexit 97\n'
    for command in DANGEROUS_COMMANDS:
        path = stub_dir / command
        path.write_text(stub, encoding="utf-8")
        path.chmod(0o755)

    env = {
        "HOME": str(tmp_path / "home"),
        "LANG": "C",
        "LC_ALL": "C",
        "LAIN5G_ALLOW_5G_NSA_RF_START": "true",
        "LAIN5G_ALLOW_5G_RF_START": "true",
        "LAIN5G_ALLOW_RF_START": "true",
        "LAIN5G_COMMAND_LOG": str(command_log),
        "LAIN5G_DRY_RUN": "true",
        "LAIN5G_RF_DURATION_SECONDS": "347",
        "LAIN5G_RF_OPERATOR_NOTE": CANARY,
        "DL_ARFCN": CANARY,
        "PATH": f"{stub_dir}:{os.environ['PATH']}",
        "REASON": CANARY,
        "REQUIRE_RF_READY": "true",
        "RX_GAIN": CANARY,
        "TMPDIR": str(sandbox_tmp),
        "TX_GAIN": CANARY,
        "USRP_ADDR": CANARY,
    }
    return sandbox, command_log, env


@pytest.mark.parametrize("script", RF_SCRIPTS, ids=lambda path: path.as_posix())
def test_every_x310_script_is_side_effect_free_in_dry_run(
    script: Path,
    rf_dry_run_sandbox: tuple[Path, Path, dict[str, str]],
):
    sandbox, command_log, env = rf_dry_run_sandbox
    before = _snapshot(sandbox)

    result = subprocess.run(
        ["bash", str(sandbox / script)],
        cwd=sandbox,
        env=env,
        text=True,
        capture_output=True,
        timeout=5,
        check=False,
    )

    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, output
    assert "DRY RUN:" in output
    assert CANARY not in output
    assert "347" not in output
    assert not re.search(r"(?i)\b(?:ARFCN|EARFCN|GAIN|FREQUENCY|PASSWORD|SERIAL|TOKEN|USRP_ADDR)\s*[:=]", output)
    assert not command_log.exists(), command_log.read_text(encoding="utf-8") if command_log.exists() else ""
    assert _snapshot(sandbox) == before


@pytest.mark.parametrize(
    ("start_script", "guard"),
    (
        (Path("deployments/4g-volte/x310/scripts/start-enb.sh"), "LAIN5G_ALLOW_RF_START"),
        (Path("deployments/5g-sa-x310/scripts/start-gnb.sh"), "LAIN5G_ALLOW_5G_RF_START"),
        (Path("deployments/5g-nsa-x310/scripts/start-rf.sh"), "LAIN5G_ALLOW_5G_NSA_RF_START"),
    ),
)
def test_dry_run_exit_precedes_normal_rf_authorization_and_start(start_script: Path, guard: str):
    source = (ROOT / start_script).read_text(encoding="utf-8")

    dry_run = source.index('if [ "${LAIN5G_DRY_RUN:-false}" = true ]')
    dry_run_exit = source.index("exit 0", dry_run)
    authorization_guard = source.index(guard, dry_run_exit)
    rf_ready_preflight = source.index("REQUIRE_RF_READY=true", authorization_guard)
    rf_service_start = source.index("docker compose", rf_ready_preflight)

    assert dry_run < dry_run_exit < authorization_guard < rf_ready_preflight < rf_service_start


@pytest.mark.parametrize(
    ("scenario", "required_guards"),
    (
        (
            Path("deployments/4g-volte/x310"),
            ("authorization", "auto_stop", "capture_logs", "operator_note", "lab_mode", "attenuation", "epc"),
        ),
        (
            Path("deployments/5g-sa-x310"),
            ("authorization", "auto_stop", "capture_logs", "operator_note", "lab_mode", "attenuation", "core_ready"),
        ),
        (
            Path("deployments/5g-nsa-x310"),
            ("authorization", "frequencies", "nr_rf_path", "operator_note", "rf_exclusive", "core_ready", "hardware"),
        ),
    ),
)
def test_normal_rf_preflight_rejects_the_blocked_default_configuration(
    scenario: Path,
    required_guards: tuple[str, ...],
):
    blocked_manifest = (ROOT / scenario / "rf/safety-manifest.example.yaml").read_text(encoding="utf-8")
    preflight = (ROOT / scenario / "scripts/preflight.sh").read_text(encoding="utf-8")

    assert "authorization_confirmed: false" in blocked_manifest
    assert "authorization" in preflight and "FAIL" in preflight
    assert "REQUIRE_RF_READY" in preflight
    assert '[ "$status" = PASS ]' in preflight
    for guard in required_guards:
        assert guard in preflight
