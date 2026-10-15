#!/usr/bin/env python3
"""Exercise 5G configuration reuse in a temporary tree, without Docker or RF."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from backend.app.services.profile_config_service import ProfileConfigService
from backend.app.settings import Settings


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="openlain5g-reuse-") as directory:
        root = Path(directory)
        for relative in ("config", "deployments/5g-sa/open5gs", "deployments/5g-sa/ueransim"):
            shutil.copytree(ROOT / relative, root / relative)
        shutil.copyfile(ROOT / "deployments/5g-sa/.env.example", root / "deployments/5g-sa/.env.example")
        shutil.copyfile(root / "deployments/5g-sa/.env.example", root / "deployments/5g-sa/.env")
        (root / "deployments/5g-sa/.env").chmod(0o600)
        service = ProfileConfigService(Settings(project_root=root, dry_run=True))
        files = lambda: {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}
        before = files()
        service.update_profile("5g-sa", {"network": {"tac": 9, "dnn": "labnet"}})
        assert service.validate_profile("5g-sa")["valid"]
        planned = sorted(f["path"] for f in service.diff_profile("5g-sa")["files"] if f["changed"])
        applied = service.apply_profile("5g-sa")
        assert sorted(applied["modified_files"]) == planned
        assert "tac: 9" in (root / "deployments/5g-sa/open5gs/amf.yaml").read_text()
        assert "labnet" in (root / "deployments/5g-sa/ueransim/ue.yaml").read_text()
        assert not any(f["changed"] for f in service.diff_profile("5g-sa")["files"])
        service.restore_profile("5g-sa")
        after = files()
        for name, content in before.items():
            if name != "config/profiles/5g-sa.yaml":
                assert after[name] == content, name
        assert (root / "deployments/5g-sa/.env").stat().st_mode & 0o777 == 0o600
        print(json.dumps({"example": "5g-sa TAC 9 and DNN labnet", "status": "PASS",
                          "scope": "configuration generation and rollback only; no network execution",
                          "planned_files": planned, "idempotent_apply": True,
                          "effective_files_restored": True}, indent=2))


if __name__ == "__main__":
    main()
