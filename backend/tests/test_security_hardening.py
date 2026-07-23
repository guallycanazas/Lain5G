from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import stat
import subprocess


ROOT = Path(__file__).resolve().parents[2]
UDM_ROLE = ROOT / "images" / "ims-real-open5gs" / "roles" / "udm"


def test_udm_keys_are_generated_at_runtime_with_private_modes(tmp_path: Path) -> None:
    generator = UDM_ROLE / "generate_hnet_keys.sh"
    assert generator.stat().st_mode & stat.S_IXUSR
    assert shutil.which("openssl") is not None

    output = tmp_path / "hnet"
    subprocess.run(
        [generator, output],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    curve_key = output / "curve25519-1.key"
    secp_key = output / "secp256r1-2.key"
    assert stat.S_IMODE(output.stat().st_mode) == 0o700
    assert stat.S_IMODE(curve_key.stat().st_mode) == 0o600
    assert stat.S_IMODE(secp_key.stat().st_mode) == 0o600

    subprocess.run(
        ["openssl", "pkey", "-in", curve_key, "-check", "-noout"],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        ["openssl", "ec", "-in", secp_key, "-check", "-noout"],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    first = (
        hashlib.sha256(curve_key.read_bytes()).digest(),
        hashlib.sha256(secp_key.read_bytes()).digest(),
    )
    subprocess.run(
        [generator, output],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    second = (
        hashlib.sha256(curve_key.read_bytes()).digest(),
        hashlib.sha256(secp_key.read_bytes()).digest(),
    )
    if any(previous == current for previous, current in zip(first, second, strict=True)):
        raise AssertionError("UDM runtime key generation reused a key")


def test_udm_packaging_excludes_private_keys() -> None:
    assert not (UDM_ROLE / "curve25519-1.key").exists()
    assert not (UDM_ROLE / "secp256r1-2.key").exists()

    init = (UDM_ROLE / "udm_init.sh").read_text(encoding="utf-8")
    assert "generate_hnet_keys.sh /open5gs/install/etc/open5gs/hnet" in init
    assert "cp /mnt/udm/curve25519" not in init
    assert "cp /mnt/udm/secp256r1" not in init

    dockerignore = (ROOT / "images" / "ims-real-open5gs" / ".dockerignore").read_text(
        encoding="utf-8"
    )
    assert "**/*.key" in dockerignore.splitlines()

    compose = (ROOT / "deployments" / "ims-real" / "compose.5g.yaml").read_text(
        encoding="utf-8"
    )
    assert "/open5gs/install/etc/open5gs/hnet:mode=0700" in compose


def test_sensitive_file_check_has_metadata_only_output() -> None:
    check = ROOT / "scripts" / "security" / "check-sensitive-files.sh"
    assert check.stat().st_mode & stat.S_IXUSR
    result = subprocess.run(
        [check],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode == 0
    assert result.stderr == ""
    records = [json.loads(line) for line in result.stdout.splitlines()]
    assert records
    assert all(
        set(record) == {"category", "path", "approx_line", "severity", "result"}
        for record in records
    )
    assert all(record["result"] == "PASS" for record in records)
