from __future__ import annotations

import os
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from ..models.deployment import CommandResult
from ..settings import Settings


SENSITIVE_KEYS = (
    "subscriber_key|subscriber_opc|subscriber_op|subscriber_sqn|subscriber_imsi|subscriber_msisdn|"
    "ims_auth_password|provisioning_key|proxy_authorization|authorization|password|passwd|token|secret|"
    "lain5g_rf_operator_note|rf_operator_note|operator_note|imsi|msisdn|supi|impi|impu|ki|opc|op|k|sqn|"
    "tx_gain|rx_gain|earfcn|arfcn|frequency_hz|frequency_mhz|mcc|mnc|tac"
)
SENSITIVE_ASSIGNMENT_RE = re.compile(
    rf"(?i)(?P<prefix>(?<![A-Za-z0-9_])[\"']?(?:{SENSITIVE_KEYS})[\"']?\s*[:=]\s*).*$"
)
URI_USERINFO_RE = re.compile(r"(?i)([a-z][a-z0-9+.-]*://)[^/@\s]+@")
SIP_USER_RE = re.compile(r"(?i)\b(sips?:)[^@\s>;]+@")
AUTH_TOKEN_RE = re.compile(r"(?i)\b(Bearer|Basic)\s+[A-Za-z0-9._~+/=-]+")
SENSITIVE_PHRASE_RE = re.compile(
    r"(?i)(?P<prefix>\b(?:operator[ _-]?note|(?:dl[ _-]?)?arfcn|earfcn|tx[ _-]?gain|rx[ _-]?gain|frequency(?:[ _-](?:hz|mhz))?)\b\s*(?::|=|is)?\s*).+$"
)
HEX_32_RE = re.compile(r"\b[0-9a-fA-F]{32}\b")
SUBSCRIBER_ID_RE = re.compile(r"(?<![\d.])\+?\d{5,20}(?![\d.])")
ENV_ASSIGNMENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=.*", re.DOTALL)

ALLOWED_DOCKER_SUBCOMMANDS = {"compose", "image", "info", "pull", "run", "tag"}
ALLOWED_COMPOSE_ACTIONS = {"logs", "version"}
ALLOWED_RUN_IMAGES = {"lain5g-lab/srsran4g-uhd:local"}
DOCKER_PATH_OPTIONS = {"-f", "--file", "--env-file", "--project-directory"}
COMPOSE_OPTIONS_WITH_VALUE = DOCKER_PATH_OPTIONS | {"-p", "--profile", "--project-name"}
RUN_OPTIONS_WITH_VALUE = {"--network", "-v", "--volume", "-w", "--workdir"}
IMAGE_REFERENCE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/:@-]{0,255}")


class CommandSecurityError(ValueError):
    pass


class CommandService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.project_root = settings.project_root.resolve()

    def execute_script(
        self,
        script: str | Path,
        *,
        cwd: str | Path | None = None,
        args: list[str] | None = None,
        dry_run: bool | None = None,
    ) -> CommandResult:
        script_path = self._resolve_inside_project(script)
        cwd_path = self._resolve_inside_project(cwd or ".")
        command = [str(script_path), *(args or [])]
        self._validate_arguments(command)
        effective_dry_run = self.settings.dry_run if dry_run is None else dry_run

        if effective_dry_run:
            return self._run(command, cwd_path, dry_run=True)

        if not script_path.exists():
            return self._synthetic_result(command, cwd_path, 127, "", f"Script not found: {self._display_path(script_path)}", dry_run=False)
        if not script_path.is_file():
            return self._synthetic_result(command, cwd_path, 126, "", "Command is not a file", dry_run=False)
        if not os.access(script_path, os.X_OK):
            return self._synthetic_result(command, cwd_path, 126, "", "Command is not executable", dry_run=False)

        return self._run(command, cwd_path, dry_run=False)

    def execute_command(
        self,
        command: list[str],
        *,
        cwd: str | Path | None = None,
        dry_run: bool | None = None,
        timeout: int | None = None,
    ) -> CommandResult:
        if not command:
            raise CommandSecurityError("Command must not be empty")
        cwd_path = self._resolve_inside_project(cwd or ".")
        self._validate_command(command, cwd_path)
        return self._run(command, cwd_path, dry_run=self.settings.dry_run if dry_run is None else dry_run, timeout=timeout)

    def redact(self, value: str) -> str:
        if isinstance(value, bytes):
            value = value.decode("utf-8", errors="replace")
        redacted_lines: list[str] = []
        for line in value.splitlines():
            line = URI_USERINFO_RE.sub(r"\1[REDACTED]@", line)
            line = SIP_USER_RE.sub(r"\1[REDACTED]@", line)
            line = AUTH_TOKEN_RE.sub(r"\1 [REDACTED]", line)
            line = SENSITIVE_ASSIGNMENT_RE.sub(r"\g<prefix>[REDACTED]", line)
            line = SENSITIVE_PHRASE_RE.sub(r"\g<prefix>[REDACTED]", line)
            line = HEX_32_RE.sub("[REDACTED]", line)
            line = SUBSCRIBER_ID_RE.sub("[REDACTED]", line)
            redacted_lines.append(line)
        return "\n".join(redacted_lines)

    def _validate_command(self, command: list[str], cwd_path: Path) -> None:
        self._validate_arguments(command)
        if command[0] == "docker":
            if len(command) < 2 or command[1] not in ALLOWED_DOCKER_SUBCOMMANDS:
                raise CommandSecurityError("Docker subcommand is not allowlisted")
            if command[1] == "compose":
                self._validate_compose_command(command, cwd_path)
            elif command[1] == "image":
                if len(command) != 4 or command[2] != "inspect" or not IMAGE_REFERENCE_RE.fullmatch(command[3]):
                    raise CommandSecurityError("Docker image command is not allowlisted")
            elif command[1] == "info":
                if len(command) > 4 or any(argument not in {"--format", "{{.ServerVersion}}"} for argument in command[2:]):
                    raise CommandSecurityError("Docker info command is not allowlisted")
            elif command[1] == "pull":
                if len(command) != 3 or not IMAGE_REFERENCE_RE.fullmatch(command[2]):
                    raise CommandSecurityError("Docker pull command is not allowlisted")
            elif command[1] == "tag":
                if len(command) != 4 or not all(IMAGE_REFERENCE_RE.fullmatch(argument) for argument in command[2:]):
                    raise CommandSecurityError("Docker tag command is not allowlisted")
            else:
                self._validate_docker_run(command, cwd_path)
            return
        if command[0] == "env":
            target_index = 1
            while target_index < len(command) and ENV_ASSIGNMENT_RE.fullmatch(command[target_index]):
                target_index += 1
            if target_index >= len(command) or not Path(command[target_index]).is_absolute():
                raise CommandSecurityError("env may execute only an absolute project script")
            self._ensure_inside_project(Path(command[target_index]).resolve())
            return
        raise CommandSecurityError("Executable is not allowlisted")

    def _validate_compose_command(self, command: list[str], cwd_path: Path) -> None:
        index = 2
        while index < len(command):
            argument = command[index]
            if argument in COMPOSE_OPTIONS_WITH_VALUE:
                if index + 1 >= len(command):
                    raise CommandSecurityError("Docker Compose option is missing a value")
                if argument in DOCKER_PATH_OPTIONS:
                    self._resolve_command_path(command[index + 1], cwd_path)
                index += 2
                continue
            if argument.startswith("-"):
                raise CommandSecurityError("Docker Compose option is not allowlisted")
            if argument not in ALLOWED_COMPOSE_ACTIONS:
                raise CommandSecurityError("Docker Compose action is not allowlisted")
            return
        raise CommandSecurityError("Docker Compose action is required")

    def _validate_docker_run(self, command: list[str], cwd_path: Path) -> None:
        index = 2
        while index < len(command):
            argument = command[index]
            if argument == "--rm":
                index += 1
                continue
            if argument in RUN_OPTIONS_WITH_VALUE:
                if index + 1 >= len(command):
                    raise CommandSecurityError("Docker run option is missing a value")
                value = command[index + 1]
                if argument in {"-v", "--volume"}:
                    self._resolve_command_path(value.split(":", 1)[0], cwd_path)
                elif argument in {"-w", "--workdir"}:
                    self._resolve_command_path(value, cwd_path)
                index += 2
                continue
            if argument.startswith("-") or argument not in ALLOWED_RUN_IMAGES:
                raise CommandSecurityError("Docker run command is not allowlisted")
            return
        raise CommandSecurityError("Docker run image is required")

    @staticmethod
    def _validate_arguments(command: list[str]) -> None:
        if any(not isinstance(argument, str) or any(char in argument for char in ("\x00", "\r", "\n")) for argument in command):
            raise CommandSecurityError("Command arguments contain unsupported control characters")

    def _resolve_command_path(self, value: str, cwd_path: Path) -> Path:
        path = Path(value)
        resolved = path.resolve() if path.is_absolute() else (cwd_path / path).resolve()
        self._ensure_inside_project(resolved)
        return resolved

    def _run(self, command: list[str], cwd_path: Path, *, dry_run: bool, timeout: int | None = None) -> CommandResult:
        started_at = datetime.now(UTC)
        if dry_run:
            finished_at = datetime.now(UTC)
            display_command = [self._display_arg(arg) for arg in command]
            return CommandResult(
                command=display_command,
                cwd=self._display_path(cwd_path),
                exit_code=0,
                stdout=f"DRY RUN: {' '.join(display_command)}",
                stderr="",
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=self._duration_ms(started_at, finished_at),
                timed_out=False,
                dry_run=True,
            )

        env = os.environ.copy()
        env["LAIN5G_DRY_RUN"] = "false"
        try:
            completed = subprocess.run(
                command,
                cwd=cwd_path,
                capture_output=True,
                text=True,
                timeout=timeout or self.settings.command_timeout,
                check=False,
                shell=False,
                env=env,
            )
            finished_at = datetime.now(UTC)
            return CommandResult(
                command=[self._display_arg(arg) for arg in command],
                cwd=self._display_path(cwd_path),
                exit_code=completed.returncode,
                stdout=self._limit_output(self.redact(completed.stdout or "")),
                stderr=self._limit_output(self.redact(completed.stderr or "")),
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=self._duration_ms(started_at, finished_at),
                timed_out=False,
                dry_run=False,
            )
        except subprocess.TimeoutExpired as exc:
            finished_at = datetime.now(UTC)
            return CommandResult(
                command=[self._display_arg(arg) for arg in command],
                cwd=self._display_path(cwd_path),
                exit_code=None,
                stdout=self._limit_output(self.redact(exc.stdout or "")),
                stderr=self._limit_output(self.redact(exc.stderr or "Command timed out")),
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=self._duration_ms(started_at, finished_at),
                timed_out=True,
                dry_run=False,
            )
        except FileNotFoundError as exc:
            return self._synthetic_result(command, cwd_path, 127, "", str(exc), dry_run=False)

    def _synthetic_result(
        self,
        command: list[str],
        cwd_path: Path,
        exit_code: int,
        stdout: str,
        stderr: str,
        *,
        dry_run: bool,
    ) -> CommandResult:
        started_at = datetime.now(UTC)
        finished_at = datetime.now(UTC)
        return CommandResult(
            command=[self._display_arg(arg) for arg in command],
            cwd=self._display_path(cwd_path),
            exit_code=exit_code,
            stdout=self._limit_output(self.redact(stdout)),
            stderr=self._limit_output(self.redact(stderr)),
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=self._duration_ms(started_at, finished_at),
            timed_out=False,
            dry_run=dry_run,
        )

    def _resolve_inside_project(self, value: str | Path) -> Path:
        path = Path(value)
        if path.is_absolute():
            resolved = path.resolve()
        else:
            resolved = (self.project_root / path).resolve()
        self._ensure_inside_project(resolved)
        return resolved

    def _ensure_inside_project(self, path: Path) -> None:
        if path != self.project_root and self.project_root not in path.parents:
            raise CommandSecurityError("Path is outside the project root")

    def _display_path(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.project_root))
        except ValueError:
            return "[outside-project]"

    def _display_arg(self, arg: str) -> str:
        try:
            display = str(Path(arg).resolve().relative_to(self.project_root))
        except (ValueError, OSError):
            display = arg
        return self.redact(display)

    def _limit_output(self, value: str) -> str:
        if len(value) <= self.settings.max_output_chars:
            return value
        omitted = len(value) - self.settings.max_output_chars
        return f"[output truncated: {omitted} chars omitted]\n" + value[-self.settings.max_output_chars :]

    @staticmethod
    def _duration_ms(started_at: datetime, finished_at: datetime) -> int:
        return int((finished_at - started_at).total_seconds() * 1000)
