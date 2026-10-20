#!/usr/bin/env python3
"""Reproduce a TAC/DNN profile adaptation without changing the source checkout."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from backend.app.services.profile_config_service import ProfileConfigService  # noqa: E402
from backend.app.services.scenario_environment import prepare_scenario_environment  # noqa: E402


PROFILE_FILES = (
    "config/profiles/5g-sa.yaml",
    "deployments/5g-sa/.env.example",
    "deployments/5g-sa/open5gs/amf.yaml",
    "deployments/5g-sa/open5gs/smf.yaml",
    "deployments/5g-sa/ueransim/gnb.yaml",
    "deployments/5g-sa/ueransim/ue.yaml",
)
MANAGED_FILES = (
    "deployments/5g-sa/.env",
    "deployments/5g-sa/open5gs/amf.yaml",
    "deployments/5g-sa/open5gs/smf.yaml",
    "deployments/5g-sa/ueransim/gnb.yaml",
    "deployments/5g-sa/ueransim/ue.yaml",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_project(destination: Path) -> None:
    for relative in PROFILE_FILES:
        source = ROOT / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def run_demo() -> dict[str, object]:
    source_hashes = {relative: digest(ROOT / relative) for relative in PROFILE_FILES}
    with tempfile.TemporaryDirectory(prefix="lain5g-profile-reuse-") as temporary:
        project = Path(temporary)
        copy_project(project)

        # Generate disposable credentials only inside the temporary project.
        prepare_scenario_environment(project, "5g-sa")
        baseline_hashes = {relative: digest(project / relative) for relative in MANAGED_FILES}
        service = ProfileConfigService(SimpleNamespace(project_root=project, dry_run=True))

        profile = service.get_profile("5g-sa")
        profile["network"]["tac"] = 9
        profile["network"]["dnn"] = "labnet"
        service.update_profile("5g-sa", profile)

        validation = service.validate_profile("5g-sa")
        if not validation["valid"]:
            raise RuntimeError("Adapted profile did not pass validation: " + "; ".join(validation["errors"]))

        preview = service.diff_profile("5g-sa")
        changed_before = [item["path"] for item in preview["files"] if item["changed"]]
        if not changed_before:
            raise RuntimeError("The TAC/DNN adaptation produced no effective configuration changes.")

        applied = service.apply_profile("5g-sa")
        applied_env = (project / "deployments/5g-sa/.env").read_text(encoding="utf-8")
        amf = (project / "deployments/5g-sa/open5gs/amf.yaml").read_text(encoding="utf-8")
        smf = (project / "deployments/5g-sa/open5gs/smf.yaml").read_text(encoding="utf-8")
        if "TAC=9" not in applied_env or "DNN=labnet" not in applied_env or "tac: 9" not in amf or "labnet" not in smf:
            raise RuntimeError("The requested TAC/DNN values did not reach the effective configuration files.")

        idempotent = not any(item["changed"] for item in service.diff_profile("5g-sa")["files"])
        if not idempotent:
            raise RuntimeError("A second preview still reports changes after applying the profile.")

        restored = service.restore_profile("5g-sa")
        restored_files = {relative: digest(project / relative) for relative in MANAGED_FILES}
        if restored_files != baseline_hashes:
            changed = [relative for relative in MANAGED_FILES if restored_files.get(relative) != baseline_hashes[relative]]
            raise RuntimeError("Restore did not return files to their pre-apply state: " + ", ".join(changed))

        source_unchanged = all(digest(ROOT / relative) == before for relative, before in source_hashes.items())
        if not source_unchanged:
            raise RuntimeError("The source checkout changed during the isolated demonstration.")

        return {
            "profile": "5g-sa",
            "adaptation": {"tac": 9, "dnn": "labnet"},
            "validation": "PASS",
            "effective_files_changed": changed_before,
            "apply": "PASS",
            "preview_after_apply": "no pending changes",
            "restore": "PASS",
            "restore_files": restored["restored_files"],
            "restore_matches_pre_apply_hashes": True,
            "source_defaults_unchanged": source_unchanged,
            "runtime_connectivity_tested": False,
            "scope": "isolated configuration adaptation and rollback; no network or RF result claimed",
            "modified_files": applied["modified_files"],
        }


if __name__ == "__main__":
    print(json.dumps(run_demo(), indent=2, sort_keys=True))
