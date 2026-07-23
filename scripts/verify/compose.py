#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass

from _common import ROOT, relative, source_files


@dataclass(frozen=True)
class ComposeCheck:
    name: str
    files: tuple[str, ...]
    env_file: str
    all_profiles: bool = False


CHECKS = (
    ComposeCheck("application", ("docker-compose.app.yml",), ".env.app.example"),
    ComposeCheck(
        "application operations override",
        ("docker-compose.app.yml", "docker-compose.app-operations.yml"),
        ".env.app.example",
    ),
    ComposeCheck(
        "4G LTE simulation",
        ("deployments/4g-lte-sim/docker-compose.yml",),
        "deployments/4g-volte/common/.env.example",
    ),
    ComposeCheck(
        "4G VoLTE simulation",
        ("deployments/4g-volte/sim/docker-compose.yml",),
        "deployments/4g-volte/common/.env.example",
        True,
    ),
    ComposeCheck(
        "4G LTE X310",
        ("deployments/4g-volte/x310/docker-compose.yml",),
        "deployments/4g-volte/common/.env.example",
        True,
    ),
    ComposeCheck(
        "5G NSA X310",
        ("deployments/5g-nsa-x310/docker-compose.yml",),
        "deployments/5g-nsa-x310/.env.example",
        True,
    ),
    ComposeCheck(
        "5G SA X310",
        ("deployments/5g-sa-x310/docker-compose.yml",),
        "deployments/5g-sa-x310/.env.example",
        True,
    ),
    ComposeCheck(
        "5G SA simulation",
        ("deployments/5g-sa/docker-compose.yml",),
        "deployments/5g-sa/.env.example",
    ),
    ComposeCheck(
        "5G VoNR simulation",
        ("deployments/5g-vonr/docker-compose.yml",),
        "deployments/5g-vonr/.env.example",
        True,
    ),
    ComposeCheck(
        "real IMS 4G",
        ("deployments/ims-real/compose.4g.yaml",),
        "deployments/ims-real/env.defaults",
    ),
    ComposeCheck(
        "real IMS 5G",
        ("deployments/ims-real/compose.5g.yaml",),
        "deployments/ims-real/env.defaults",
    ),
)

SAFE_SERVICE_ENVS = {
    "deployments/4g-volte/common/.env": "deployments/4g-volte/common/.env.example",
    "deployments/5g-sa/.env": "deployments/5g-sa/.env.example",
    "deployments/5g-vonr/.env": "deployments/5g-vonr/.env.example",
}


def _source_compose_files() -> set[str]:
    return {
        relative(path)
        for path in source_files()
        if path.suffix.lower() in {".yaml", ".yml"} and "compose" in path.name.lower()
    }


def main() -> int:
    discovered = _source_compose_files()
    covered = {path for check in CHECKS for path in check.files}
    errors = [f"unmapped source Compose file: {path}" for path in sorted(discovered - covered)]
    errors.extend(f"mapped Compose file is missing: {path}" for path in sorted(covered - discovered))

    with tempfile.TemporaryDirectory(prefix="lain5g-compose-verify-") as temporary:
        verification_root = Path(temporary) / "source"
        inputs = {path for check in CHECKS for path in (*check.files, check.env_file)}
        for relative_path in sorted(inputs):
            source = ROOT / relative_path
            if not source.is_file():
                continue
            target = verification_root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        for target_path, example_path in SAFE_SERVICE_ENVS.items():
            source = ROOT / example_path
            if not source.is_file():
                errors.append(f"safe service environment input is missing: {example_path}")
                continue
            target = verification_root / target_path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        env = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": temporary,
            "DOCKER_CONFIG": temporary,
            "DOCKER_HOST": f"unix://{temporary}/docker-socket-does-not-exist",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
        }
        version = subprocess.run(
            ["docker", "compose", "version"],
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if version.returncode != 0:
            errors.append("Docker Compose v2 is unavailable; source configurations were not validated")
        else:
            for check in CHECKS:
                source_env_path = ROOT / check.env_file
                if not source_env_path.is_file():
                    errors.append(f"{check.name}: safe environment input is missing: {check.env_file}")
                    continue
                env_path = verification_root / check.env_file
                command = ["docker", "compose", "--env-file", str(env_path)]
                for compose_file in check.files:
                    command.extend(("-f", str(verification_root / compose_file)))
                if check.all_profiles:
                    command.extend(("--profile", "*"))
                command.extend(("config", "--quiet", "--no-env-resolution"))
                result = subprocess.run(
                    command,
                    cwd=verification_root,
                    env=env,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                if result.returncode != 0:
                    detail = result.stderr.strip() or "docker compose config failed"
                    errors.append(f"{check.name}: {detail}")

    if errors:
        print(f"compose-check: FAIL ({len(errors)} error(s))", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        f"compose-check: OK ({len(discovered)} source files, {len(CHECKS)} safe configs; "
        "all profiles, --no-env-resolution, no Docker socket)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
