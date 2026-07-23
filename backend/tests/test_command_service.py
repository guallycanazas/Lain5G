import os
import subprocess
from pathlib import Path

import pytest

from backend.app.services.command_service import CommandSecurityError, CommandService


def write_script(path: Path, content: str, executable: bool = True) -> Path:
    path.write_text(content, encoding="utf-8")
    if executable:
        path.chmod(0o755)
    return path


def test_executes_safe_command_and_captures_output(project_root, real_settings):
    script = write_script(project_root / "safe.sh", '#!/usr/bin/env bash\necho "hello"\necho "warn" >&2\nexit 3\n')
    service = CommandService(real_settings)

    result = service.execute_script(script)

    assert result.exit_code == 3
    assert result.stdout.strip() == "hello"
    assert result.stderr.strip() == "warn"
    assert result.dry_run is False


def test_handles_timeout(project_root, real_settings):
    script = write_script(project_root / "slow.sh", '#!/usr/bin/env bash\nsleep 2\n')
    service = CommandService(real_settings)

    result = service.execute_script(script)

    assert result.timed_out is True
    assert result.exit_code is None


def test_rejects_script_outside_project(real_settings):
    service = CommandService(real_settings)


    with pytest.raises(CommandSecurityError):
        service.execute_script("/bin/sh")


def test_rejects_symlink_to_external_path(project_root, real_settings):
    link = project_root / "external.sh"
    link.symlink_to("/bin/sh")
    service = CommandService(real_settings)

    with pytest.raises(CommandSecurityError):
        service.execute_script(link)


def test_never_uses_shell(project_root, real_settings, monkeypatch):
    script = write_script(project_root / "shell-check.sh", '#!/usr/bin/env bash\necho ok\n')
    service = CommandService(real_settings)
    observed = {}

    def fake_run(*args, **kwargs):
        observed["shell"] = kwargs.get("shell")
        return subprocess.CompletedProcess(args=args[0], returncode=0, stdout="ok\n", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = service.execute_script(script)

    assert result.exit_code == 0
    assert observed["shell"] is False


def test_redacts_known_secrets(project_root, real_settings):
    script = write_script(
        project_root / "secret.sh",
        '#!/usr/bin/env bash\necho "SUBSCRIBER_KEY=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"\necho "OPC: bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb" >&2\n',
    )
    service = CommandService(real_settings)

    result = service.execute_script(script)

    assert "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" not in result.stdout
    assert "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb" not in result.stderr
    assert "[REDACTED]" in result.stdout
    assert "[REDACTED]" in result.stderr


def test_limits_excessive_output(project_root, real_settings):
    script = write_script(project_root / "large.sh", '#!/usr/bin/env bash\npython3 -c "print(\'x\'*2000)"\n')
    service = CommandService(real_settings)

    result = service.execute_script(script)

    assert result.stdout.startswith("[output truncated:")
    assert len(result.stdout) < 1100


def test_handles_non_executable_file(project_root, real_settings):
    script = write_script(project_root / "not-exec.sh", '#!/usr/bin/env bash\necho no\n', executable=False)
    service = CommandService(real_settings)

    result = service.execute_script(script)

    assert result.exit_code == 126


def test_rejects_unauthorized_executable(real_settings):
    service = CommandService(real_settings)

    with pytest.raises(CommandSecurityError, match="not allowlisted"):
        service.execute_command(["definitely-missing-lain5g-command"])


def test_rejects_unauthorized_docker_subcommand(real_settings):
    service = CommandService(real_settings)

    with pytest.raises(CommandSecurityError, match="subcommand"):
        service.execute_command(["docker", "system", "prune"])


def test_rejects_unauthorized_compose_action(real_settings):
    service = CommandService(real_settings)

    with pytest.raises(CommandSecurityError, match="action"):
        service.execute_command(["docker", "compose", "up", "-d"])


def test_rejects_compose_file_path_traversal(real_settings):
    service = CommandService(real_settings)

    with pytest.raises(CommandSecurityError, match="outside"):
        service.execute_command(["docker", "compose", "-f", "../../compose.yml", "logs"])


def test_rejects_path_traversal_in_cwd(real_settings):
    service = CommandService(real_settings)

    with pytest.raises(CommandSecurityError, match="outside"):
        service.execute_command(["docker", "info"], cwd="../../")


def test_rejects_env_execution_outside_project(real_settings):
    service = CommandService(real_settings)

    with pytest.raises(CommandSecurityError, match="outside"):
        service.execute_command(["env", "SAFE=value", "/bin/sh"])


def test_dry_run_does_not_execute(project_root, dry_settings):
    marker = project_root / "marker"
    script = write_script(project_root / "touch-marker.sh", f'#!/usr/bin/env bash\ntouch "{marker}"\n')
    service = CommandService(dry_settings)

    result = service.execute_script(script)

    assert result.dry_run is True
    assert not marker.exists()


def test_timeout_output_is_redacted_and_limited(project_root, real_settings, monkeypatch):
    script = write_script(project_root / "timeout.sh", "#!/usr/bin/env bash\nexit 0\n")
    service = CommandService(real_settings)
    secret = "00112233445566778899AABBCCDDEEFF"

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], 1, output=f"IMSI=001010000000001\n{'x' * 1200}", stderr=f"Authorization: Bearer {secret}")

    monkeypatch.setattr(subprocess, "run", timeout)
    result = service.execute_script(script)

    assert result.timed_out is True
    assert "001010000000001" not in result.stdout
    assert secret not in result.stderr
    assert "[REDACTED]" in result.stderr
    assert result.stdout.startswith("[output truncated:")


def test_redacts_uri_credentials_sip_users_identifiers_rf_values_and_notes(real_settings):
    service = CommandService(real_settings)
    value = "\n".join(
        [
            "database=mongodb://user:password@mongo:27017/open5gs",
            "contact=sip:001010000000001@example.invalid",
            "MSISDN=15551234567",
            "TX_GAIN=42",
            "LAIN5G_RF_OPERATOR_NOTE=private operator note",
            "EARFCN 3400",
            "operator note: second private note",
        ]
    )

    redacted = service.redact(value)

    for sensitive in ("user:", "password", "001010000000001", "15551234567", "42", "private operator note", "3400", "second private note"):
        assert sensitive not in redacted
    assert redacted.count("[REDACTED]") >= 7
