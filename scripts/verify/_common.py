from __future__ import annotations

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def source_files(root: Path = ROOT) -> tuple[Path, ...]:
    """Return tracked and versionable untracked files from the current tree."""
    result = subprocess.run(
        [
            "git",
            "-C",
            os.fspath(root),
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
            "--",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"cannot enumerate the current Git tree: {detail}")

    files: list[Path] = []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        relative = Path(os.fsdecode(raw))
        path = root / relative
        if path.is_file() and not path.is_symlink():
            files.append(path)
    return tuple(sorted(files))


def relative(path: Path, root: Path = ROOT) -> str:
    return path.relative_to(root).as_posix()
