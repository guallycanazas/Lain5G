from __future__ import annotations

import fcntl
import os
import secrets
import tempfile
from pathlib import Path


SCENARIO_ENVIRONMENTS = {
    "4g-lte-sim": ("deployments/4g-volte/common", ("SUBSCRIBER_KEY", "SUBSCRIBER_OPC")),
    "4g-volte-sim": ("deployments/4g-volte/common", ("SUBSCRIBER_KEY", "SUBSCRIBER_OPC", "IMS_AUTH_PASSWORD")),
    "4g-lte-x310": ("deployments/4g-volte/common", ("SUBSCRIBER_KEY", "SUBSCRIBER_OPC", "IMS_AUTH_PASSWORD")),
    "5g-sa": ("deployments/5g-sa", ("SUBSCRIBER_KEY", "SUBSCRIBER_OPC")),
    "5g-sa-x310": ("deployments/5g-sa-x310", ("IMS_AUTH_PASSWORD",)),
    "5g-vonr": ("deployments/5g-vonr", ("SUBSCRIBER_KEY", "SUBSCRIBER_OPC", "IMS_AUTH_PASSWORD")),
}


def prepare_scenario_environment(project_root: Path, profile_id: str) -> tuple[Path, bool]:
    root = project_root.resolve()
    lock_fd = os.open(root, os.O_RDONLY)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        return _prepare_scenario_environment(project_root, profile_id)
    finally:
        os.close(lock_fd)


def _prepare_scenario_environment(project_root: Path, profile_id: str) -> tuple[Path, bool]:
    profile_id = "5g-vonr" if profile_id == "5g-vonr-sim" else profile_id
    if profile_id not in SCENARIO_ENVIRONMENTS:
        raise ValueError(f"Unsupported software profile: {profile_id}")

    root = project_root.resolve()
    directory, required_secrets = SCENARIO_ENVIRONMENTS[profile_id]
    environment_dir = (root / directory).resolve()
    if not environment_dir.is_relative_to(root):
        raise OSError("Scenario environment directory escapes the project root")
    example = environment_dir / ".env.example"
    target = environment_dir / ".env"
    if example.is_symlink() or target.is_symlink():
        raise OSError("Scenario environment files must not be symbolic links")

    source = target if target.is_file() else example
    text = source.read_text(encoding="utf-8")
    current: dict[str, tuple[str, str]] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, value = line.split("=", 1)
        raw_value = value.strip()
        current[key.strip()] = (raw_value.strip("\"'"), raw_value)

    values = {
        key: current[key][1] if key in current and current[key][0] else secrets.token_hex(16)
        for key in required_secrets
    }
    lines = text.splitlines()
    for key, value in values.items():
        replacement = f"{key}={value}"
        found = False
        normalized = []
        for line in lines:
            candidate = line.lstrip()
            if candidate.startswith("export "):
                candidate = candidate[7:].lstrip()
            if candidate.startswith(f"{key}="):
                if not found:
                    normalized.append(replacement)
                    found = True
                continue
            normalized.append(line)
        if not found:
            normalized.append(replacement)
        lines = normalized

    updated = "\n".join(lines) + "\n"
    changed = not target.is_file() or target.read_text(encoding="utf-8") != updated
    temporary_path: Path | None = None
    try:
        if changed:
            owner = source.stat()
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=target.parent,
                prefix=".env.",
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                temporary.write(updated)
                temporary.flush()
                os.fsync(temporary.fileno())
            temporary_path.chmod(0o600)
            if os.geteuid() == 0:
                os.chown(temporary_path, owner.st_uid, owner.st_gid)
            os.replace(temporary_path, target)
            temporary_path = None
        target.chmod(0o600)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return target, changed
