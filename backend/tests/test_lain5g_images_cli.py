from __future__ import annotations

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def fake_docker(tmp_path: Path) -> tuple[dict[str, str], Path]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log_path = tmp_path / "docker.log"
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/usr/bin/env bash\n"
        "printf '%s\\n' \"$*\" >> \"$DOCKER_COMMAND_LOG\"\n"
        "if [ \"${1:-}\" = image ] && [ \"${2:-}\" = inspect ]; then exit 1; fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    docker.chmod(0o755)
    env = {
        **os.environ,
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "DOCKER_COMMAND_LOG": str(log_path),
    }
    return env, log_path


def test_images_pull_downloads_and_tags_without_building_or_starting(tmp_path: Path):
    env, log_path = fake_docker(tmp_path)
    result = subprocess.run(
        [str(ROOT / "lain5g"), "images", "pull", "4g-lte-sim"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    commands = log_path.read_text(encoding="utf-8").splitlines()
    assert "pull gually/lain5g-open5gs:2.7.5-lain1@sha256:d25affe90c39adb35bfef312e725b27d2ef6b139ec1d8b2fe9f5d0da6d82753c" in commands
    assert "tag gually/lain5g-open5gs:2.7.5-lain1@sha256:d25affe90c39adb35bfef312e725b27d2ef6b139ec1d8b2fe9f5d0da6d82753c lain5g-lab/open5gs:local" in commands
    assert "pull gually/lain5g-srsran4g-sim:23.11-lain1@sha256:7ec771cf70e77f699283017b02bbe6311fd377047109dc952c2c18ebae1e2ced" in commands
    assert "tag gually/lain5g-srsran4g-sim:23.11-lain1@sha256:7ec771cf70e77f699283017b02bbe6311fd377047109dc952c2c18ebae1e2ced lain5g-lab/srsran4g-sim:local" in commands
    assert "pull mongo@sha256:8b6d8f5bbedb25cb73517b65cf99f13aeb75ad5b157a56c479287a840bbad3ac" in commands
    assert not any("build" in command or "push" in command or " up" in command for command in commands)
    assert "No se compilo ninguna imagen" in result.stdout


def test_images_command_rejects_unknown_profile_before_docker(tmp_path: Path):
    env, log_path = fake_docker(tmp_path)
    result = subprocess.run(
        [str(ROOT / "lain5g"), "images", "pull", "../../otro"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "Perfil desconocido" in result.stderr
    assert not log_path.exists()


def test_main_menu_exposes_preparation_without_publishing():
    result = subprocess.run(
        [str(ROOT / "lain5g")],
        cwd=ROOT,
        input="0\n",
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Imagenes y componentes" in result.stdout
    assert "Revisar equipo y dependencias" in result.stdout
    assert "publicar" not in result.stdout.lower()
