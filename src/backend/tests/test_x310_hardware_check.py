from __future__ import annotations

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CHECK = ROOT / "deployments" / "4g-volte" / "x310" / "scripts" / "hardware-check.sh"


def run_hardware_check(tmp_path: Path, route: str, *, wireless: bool = False) -> str:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    stubs = {
        "ip": 'printf "%s\\n" "$MOCK_ROUTE"\n',
        "ping": "exit 0\n",
        "uhd_find_devices": 'printf "type: x300\\naddr: 172.30.8.2\\n"\n',
    }
    for name, content in stubs.items():
        path = bin_dir / name
        path.write_text(f"#!/bin/sh\n{content}", encoding="utf-8")
        path.chmod(0o755)

    env_file = tmp_path / "common.env"
    env_file.write_text("USRP_ADDR=172.30.8.2\n", encoding="utf-8")
    interface = tmp_path / "sys" / "class" / "net" / "enp-test"
    (interface / "device").mkdir(parents=True, exist_ok=True)
    (interface / "carrier").write_text("1\n", encoding="utf-8")
    if wireless:
        (interface / "wireless").mkdir(exist_ok=True)

    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{bin_dir}:{env['PATH']}",
            "MOCK_ROUTE": route,
            "LAIN5G_COMMON_ENV_FILE": str(env_file),
            "LAIN5G_SYS_CLASS_NET": str(interface.parent),
            "LAIN5G_UHD_DISCOVERY_LOG": str(tmp_path / "uhd-discovery.log"),
        }
    )
    result = subprocess.run(
        ["bash", str(CHECK)],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def test_4g_hardware_check_accepts_direct_wired_route_on_another_subnet(tmp_path: Path):
    output = run_hardware_check(
        tmp_path,
        "172.30.8.2 dev enp-test src 172.30.8.1 uid 1000",
    )

    ethernet = next(line for line in output.splitlines() if line.startswith("ethernet_link"))
    assert "PASS direct route to 172.30.8.2" in ethernet
    assert "wired interface enp-test at 172.30.8.1; link carrier is up" in ethernet
    ping = next(line for line in output.splitlines() if line.startswith("x310_ping"))
    uhd = next(line for line in output.splitlines() if line.startswith("uhd_find_devices"))
    assert "PASS X310 responds at 172.30.8.2" in ping
    assert "PASS X310/X300 family device found" in uhd
    assert "status=PASS" in output


def test_4g_hardware_check_does_not_call_gateway_or_wifi_an_ethernet_link(tmp_path: Path):
    gateway_output = run_hardware_check(
        tmp_path,
        "172.30.8.2 via 172.30.8.254 dev enp-test src 172.30.8.1 uid 1000",
    )
    gateway_ethernet = next(line for line in gateway_output.splitlines() if line.startswith("ethernet_link"))
    assert "WARNING route to 172.30.8.2 uses gateway" in gateway_ethernet

    wifi_output = run_hardware_check(
        tmp_path,
        "172.30.8.2 dev enp-test src 172.30.8.1 uid 1000",
        wireless=True,
    )
    wifi_ethernet = next(line for line in wifi_output.splitlines() if line.startswith("ethernet_link"))
    assert "WARNING route to 172.30.8.2 uses wireless interface" in wifi_ethernet
