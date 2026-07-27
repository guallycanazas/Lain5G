from __future__ import annotations

import fcntl
import os
import subprocess
from pathlib import Path

import pytest


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


def fake_app_tools(tmp_path: Path, project_root: Path) -> tuple[dict[str, str], Path, Path]:
    bin_dir = tmp_path / "app-bin"
    bin_dir.mkdir()
    make_log = tmp_path / "make.log"
    open_log = tmp_path / "open.log"
    for name, log_variable, exit_variable in (
        ("make", "MAKE_COMMAND_LOG", "MAKE_EXIT_CODE"),
        ("xdg-open", "OPEN_COMMAND_LOG", "OPEN_EXIT_CODE"),
    ):
        executable = bin_dir / name
        executable.write_text(
            "#!/usr/bin/env bash\n"
            f"printf '%s\\n' \"$*\" >> \"${{{log_variable}}}\"\n"
            f"exit \"${{{exit_variable}:-0}}\"\n",
            encoding="utf-8",
        )
        executable.chmod(0o755)
    env = {
        **os.environ,
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "LAIN5G_PROJECT_ROOT": str(project_root),
        "MAKE_COMMAND_LOG": str(make_log),
        "OPEN_COMMAND_LOG": str(open_log),
    }
    return env, make_log, open_log


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
    assert "Aplicacion web" in result.stdout
    assert "Revisar equipo y dependencias" in result.stdout
    assert "publicar" not in result.stdout.lower()


def test_app_setup_creates_private_safe_configuration(tmp_path: Path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / ".env.app.example").write_text(
        (ROOT / ".env.app.example").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (project_root / ".env.app").write_text(
        (project_root / ".env.app.example")
        .read_text(encoding="utf-8")
        + "LAIN5G_MUTATING_OPERATIONS_ENABLED=true\n"
        + "LAIN5G_IMAGE_PULL_ENABLED=true\n"
        + "export LAIN5G_RF_WEB_CONTROL_ENABLED=true\n",
        encoding="utf-8",
    )
    env, make_log, _ = fake_app_tools(tmp_path, project_root)

    result = subprocess.run(
        [str(ROOT / "lain5g"), "app", "setup"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    configured = project_root / ".env.app"
    text = configured.read_text(encoding="utf-8")
    assert f"LAIN5G_PROJECT_ROOT={project_root}" in text
    assert "LAIN5G_MUTATING_OPERATIONS_ENABLED=false" in text
    assert "LAIN5G_IMAGE_PULL_ENABLED=false" in text
    assert "LAIN5G_RF_WEB_CONTROL_ENABLED=false" in text
    assert text.count("LAIN5G_MUTATING_OPERATIONS_ENABLED=") == 1
    assert text.count("LAIN5G_IMAGE_PULL_ENABLED=") == 1
    assert text.count("LAIN5G_RF_WEB_CONTROL_ENABLED=") == 1
    assert configured.stat().st_mode & 0o777 == 0o600
    assert make_log.read_text(encoding="utf-8").splitlines() == ["app-down-operations"]


def test_app_operational_start_enables_software_and_guarded_rf_operations(tmp_path: Path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / ".env.app.example").write_text(
        (ROOT / ".env.app.example").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    env, make_log, open_log = fake_app_tools(tmp_path, project_root)

    result = subprocess.run(
        [str(ROOT / "lain5g"), "app", "start", "--operations", "--open"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    text = (project_root / ".env.app").read_text(encoding="utf-8")
    assert "LAIN5G_MUTATING_OPERATIONS_ENABLED=true" in text
    assert "LAIN5G_IMAGE_PULL_ENABLED=true" in text
    assert "LAIN5G_RF_WEB_CONTROL_ENABLED=true" in text
    assert make_log.read_text(encoding="utf-8").splitlines() == ["app-up-operations"]
    assert open_log.read_text(encoding="utf-8").splitlines() == ["http://127.0.0.1:8080"]


@pytest.mark.parametrize("arguments", (("stop",), ("start", "--open")))
def test_app_refuses_to_remove_emergency_control_during_active_rf(tmp_path: Path, arguments: tuple[str, ...]):
    project_root = tmp_path / "project"
    marker = project_root / "deployments/5g-sa-x310/.rf-active"
    marker.parent.mkdir(parents=True)
    marker.write_text("run_id=test\n", encoding="utf-8")
    env, make_log, _ = fake_app_tools(tmp_path, project_root)

    result = subprocess.run(
        [str(ROOT / "lain5g"), "app", *arguments],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "parada de emergencia" in result.stderr
    assert not make_log.exists()


def test_app_downgrade_stops_operational_stack_before_safe_start(tmp_path: Path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    template = (ROOT / ".env.app.example").read_text(encoding="utf-8")
    (project_root / ".env.app.example").write_text(template, encoding="utf-8")
    (project_root / ".env.app").write_text(
        template.replace("LAIN5G_MUTATING_OPERATIONS_ENABLED=false", "LAIN5G_MUTATING_OPERATIONS_ENABLED=true"),
        encoding="utf-8",
    )
    env, make_log, _ = fake_app_tools(tmp_path, project_root)

    result = subprocess.run(
        [str(ROOT / "lain5g"), "app", "start", "--open"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert make_log.read_text(encoding="utf-8").splitlines() == ["app-down-operations", "app-up"]
    assert "LAIN5G_MUTATING_OPERATIONS_ENABLED=false" in (project_root / ".env.app").read_text(encoding="utf-8")


def test_app_transition_rejects_concurrent_rf_start(tmp_path: Path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    env, make_log, _ = fake_app_tools(tmp_path, project_root)
    lock_fd = os.open(project_root, os.O_RDONLY)
    fcntl.flock(lock_fd, fcntl.LOCK_EX)
    try:
        result = subprocess.run(
            [str(ROOT / "lain5g"), "app", "stop"],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
    finally:
        os.close(lock_fd)

    assert result.returncode == 1
    assert "inicio RF en curso" in result.stderr
    assert not make_log.exists()


def test_app_setup_rejects_symlink_environment(tmp_path: Path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / ".env.app.example").write_text(
        (ROOT / ".env.app.example").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    outside = tmp_path / "outside.env"
    outside.write_text("DO_NOT_CHANGE=true\n", encoding="utf-8")
    (project_root / ".env.app").symlink_to(outside)
    env, _, _ = fake_app_tools(tmp_path, project_root)

    result = subprocess.run(
        [str(ROOT / "lain5g"), "app", "setup"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "enlace simbolico" in result.stderr
    assert outside.read_text(encoding="utf-8") == "DO_NOT_CHANGE=true\n"


def test_app_start_stays_successful_when_browser_cannot_open(tmp_path: Path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / ".env.app.example").write_text(
        (ROOT / ".env.app.example").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    env, make_log, _ = fake_app_tools(tmp_path, project_root)
    env["OPEN_EXIT_CODE"] = "7"

    result = subprocess.run(
        [str(ROOT / "lain5g"), "app", "start", "--open"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert make_log.read_text(encoding="utf-8").splitlines() == ["app-up"]
    assert "aplicacion esta iniciada" in result.stdout


@pytest.mark.parametrize(
    ("action", "target"),
    (("status", "app-ps-operations"), ("logs", "app-logs-operations"), ("stop", "app-down-operations")),
)
def test_app_management_uses_complete_compose_definition(tmp_path: Path, action: str, target: str):
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / ".env.app").write_text(
        f"LAIN5G_PROJECT_ROOT={project_root}\nLAIN5G_MUTATING_OPERATIONS_ENABLED=false\nAPP_FRONTEND_PORT=8080\n",
        encoding="utf-8",
    )
    env, make_log, _ = fake_app_tools(tmp_path, project_root)

    result = subprocess.run(
        [str(ROOT / "lain5g"), "app", action],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert make_log.read_text(encoding="utf-8").splitlines() == [target]


def test_operational_make_target_cleans_inherited_environment_before_compose():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    target = makefile.split("app-up-operations:", 1)[1].split("app-down-operations:", 1)[0]

    assert "APP_CLEAN_ENV := env" in makefile
    clean_env = next(line for line in makefile.splitlines() if line.startswith("APP_CLEAN_ENV :="))
    for variable in (
        "COMPOSE_PROJECT_NAME",
        "COMPOSE_FILE",
        "COMPOSE_PROFILES",
        "LAIN5G_PROJECT_ROOT",
        "LAIN5G_MUTATING_OPERATIONS_ENABLED",
        "LAIN5G_IMAGE_PULL_ENABLED",
        "LAIN5G_RF_WEB_CONTROL_ENABLED",
        "APP_FRONTEND_PORT",
    ):
        assert f"-u {variable}" in clean_env
    assert "$(APP_CLEAN_ENV) docker compose" in target
    assert "$(APP_CLEAN_ENV) ./lain5g app setup --operations" not in target


@pytest.mark.parametrize(
    ("profile", "target"),
    (
        ("4g-lte-sim", "start-4g-lte-sim"),
        ("4g-volte-sim", "start-4g-volte-sim"),
        ("5g-sa", "start-5g-sa"),
        ("5g-vonr", "start-5g-vonr-sim"),
    ),
)
def test_guided_console_prepares_and_starts_every_software_profile(tmp_path: Path, profile: str, target: str):
    bin_dir = tmp_path / "console-bin"
    bin_dir.mkdir()
    make_log = tmp_path / "make.log"
    project_root = tmp_path / "project"
    profiles_dir = project_root / "config/profiles"
    profiles_dir.mkdir(parents=True)
    (profiles_dir / f"{profile}.yaml").write_text(
        (ROOT / "config/profiles" / f"{profile}.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    environment_directory = {
        "4g-lte-sim": "deployments/4g-volte/common",
        "4g-volte-sim": "deployments/4g-volte/common",
        "5g-sa": "deployments/5g-sa",
        "5g-vonr": "deployments/5g-vonr",
    }[profile]
    environment_dir = project_root / environment_directory
    environment_dir.mkdir(parents=True)
    (environment_dir / ".env.example").write_text(
        (ROOT / environment_directory / ".env.example").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    for name in ("docker", "make"):
        executable = bin_dir / name
        executable.write_text(
            "#!/usr/bin/env bash\n"
            + ("printf '%s\\n' \"$*\" >> \"$MAKE_COMMAND_LOG\"\n" if name == "make" else "")
            + "exit 0\n",
            encoding="utf-8",
        )
        executable.chmod(0o755)
    env = {
        **os.environ,
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "MAKE_COMMAND_LOG": str(make_log),
        "LAIN5G_PROJECT_ROOT": str(project_root),
    }

    result = subprocess.run(
        [str(ROOT / "lain5g"), "profile", "wizard", profile],
        cwd=ROOT,
        env=env,
        input="1\n\n0\n",
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert make_log.read_text(encoding="utf-8").splitlines() == [target]
    assert (environment_dir / ".env").stat().st_mode & 0o777 == 0o600


def test_guided_console_dry_run_does_not_create_credentials(tmp_path: Path):
    project_root = tmp_path / "project"
    profiles_dir = project_root / "config/profiles"
    profiles_dir.mkdir(parents=True)
    (profiles_dir / "5g-sa.yaml").write_text(
        (ROOT / "config/profiles/5g-sa.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name in ("docker", "make"):
        executable = bin_dir / name
        executable.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        executable.chmod(0o755)
    env = {
        **os.environ,
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "LAIN5G_PROJECT_ROOT": str(project_root),
        "LAIN5G_DRY_RUN": "true",
    }

    result = subprocess.run(
        [str(ROOT / "lain5g"), "profile", "wizard", "5g-sa"],
        cwd=ROOT,
        env=env,
        input="1\n\n0\n",
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert not (project_root / "deployments/5g-sa/.env").exists()


def test_direct_scenario_command_starts_software_profile(tmp_path: Path):
    bin_dir = tmp_path / "scenario-bin"
    bin_dir.mkdir()
    make_log = tmp_path / "make.log"
    project_root = tmp_path / "project"
    environment_dir = project_root / "deployments/5g-vonr"
    environment_dir.mkdir(parents=True)
    (environment_dir / ".env.example").write_text(
        (ROOT / "deployments/5g-vonr/.env.example").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    for name in ("docker", "make"):
        executable = bin_dir / name
        executable.write_text(
            "#!/usr/bin/env bash\n"
            + ("printf '%s\\n' \"$*\" >> \"$MAKE_COMMAND_LOG\"\n" if name == "make" else "")
            + "exit 0\n",
            encoding="utf-8",
        )
        executable.chmod(0o755)
    env = {
        **os.environ,
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "MAKE_COMMAND_LOG": str(make_log),
        "LAIN5G_PROJECT_ROOT": str(project_root),
    }

    result = subprocess.run(
        [str(ROOT / "lain5g"), "scenario", "start", "5g-vonr-sim"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert make_log.read_text(encoding="utf-8").splitlines() == ["start-5g-vonr-sim"]
    assert (environment_dir / ".env").stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize(
    ("profile", "directory", "requires_ims_password"),
    (
        ("4g-lte-sim", "deployments/4g-volte/common", True),
        ("5g-sa", "deployments/5g-sa", False),
        ("5g-vonr-sim", "deployments/5g-vonr", True),
        ("4g-volte-sim", "deployments/4g-volte/common", True),
    ),
)
def test_scenario_setup_generates_private_synthetic_credentials(
    tmp_path: Path,
    profile: str,
    directory: str,
    requires_ims_password: bool,
):
    project_root = tmp_path / "project"
    environment_dir = project_root / directory
    environment_dir.mkdir(parents=True)
    source_directory = "deployments/5g-vonr" if profile == "5g-vonr-sim" else directory
    (environment_dir / ".env.example").write_text(
        (ROOT / source_directory / ".env.example").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    if requires_ims_password:
        (environment_dir / ".env").write_text(
            (environment_dir / ".env.example")
            .read_text(encoding="utf-8")
            .replace("IMS_AUTH_PASSWORD=", "IMS_AUTH_PASSWORD='secret value'"),
            encoding="utf-8",
        )
    env = {**os.environ, "LAIN5G_PROJECT_ROOT": str(project_root)}

    first = subprocess.run(
        [str(ROOT / "lain5g"), "scenario", "setup", profile],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert first.returncode == 0
    target = environment_dir / ".env"
    original = target.read_text(encoding="utf-8")
    values = dict(
        line.split("=", 1)
        for line in original.splitlines()
        if line and not line.startswith("#") and "=" in line
    )
    assert len(values["SUBSCRIBER_KEY"]) == 32
    assert len(values["SUBSCRIBER_OPC"]) == 32
    int(values["SUBSCRIBER_KEY"], 16)
    int(values["SUBSCRIBER_OPC"], 16)
    assert values["SUBSCRIBER_KEY"] != values["SUBSCRIBER_OPC"]
    assert bool(values.get("IMS_AUTH_PASSWORD")) is requires_ims_password
    if requires_ims_password:
        assert "IMS_AUTH_PASSWORD='secret value'" in original
    assert target.stat().st_mode & 0o777 == 0o600
    assert values["SUBSCRIBER_KEY"] not in first.stdout
    assert values["SUBSCRIBER_OPC"] not in first.stdout

    second = subprocess.run(
        [str(ROOT / "lain5g"), "scenario", "setup", profile],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert second.returncode == 0
    assert target.read_text(encoding="utf-8") == original


def test_direct_scenario_start_requires_explicit_image_pull(tmp_path: Path):
    env, docker_log = fake_docker(tmp_path)

    result = subprocess.run(
        [str(ROOT / "lain5g"), "scenario", "start", "5g-sa"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "./lain5g images pull 5g-sa" in result.stderr
    assert not any(line.startswith("pull ") for line in docker_log.read_text(encoding="utf-8").splitlines())
