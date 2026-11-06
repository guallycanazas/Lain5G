from __future__ import annotations

from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[3]
LOADER = SourceFileLoader("lain5g_manager_cli", str(ROOT / "lain5g"))
SPEC = spec_from_loader("lain5g_manager_cli", LOADER)
assert SPEC is not None and SPEC.loader is not None
CLI = module_from_spec(SPEC)
SPEC.loader.exec_module(CLI)


def test_stable_version_parser_sorts_numeric_components(monkeypatch):
    remote = subprocess.CompletedProcess(
        ["git"],
        0,
        "a1\trefs/tags/v1.9.0\na2\trefs/tags/v1.10.0\na3\trefs/tags/v1.10.0-rc1\n",
        "",
    )
    monkeypatch.setattr(CLI, "_git_result", lambda *_args: remote)

    tags, error = CLI._remote_stable_tags(Path("/not/a/repository"))

    assert error is None
    assert tags == ["v1.10.0", "v1.9.0"]


def test_version_check_reports_remote_latest_without_switching(tmp_path: Path, monkeypatch, capsys):
    (tmp_path / "VERSION").write_text("1.1.8\n", encoding="utf-8")
    monkeypatch.setattr(CLI, "_remote_stable_tags", lambda _root: (["v1.1.9", "v1.1.8"], None))

    result = CLI._version_command(SimpleNamespace(root=tmp_path), ["check"])

    assert result == 0
    assert "Version estable mas reciente: v1.1.9" in capsys.readouterr().out


def test_version_switch_dry_run_has_no_git_mutation(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setattr(CLI, "_remote_stable_tags", lambda _root: (["v1.1.9"], None))
    monkeypatch.setattr(CLI, "_version_switch_preflight", lambda _root: True)
    monkeypatch.setattr(
        CLI,
        "_git_result",
        lambda *_args: pytest.fail("dry-run must not fetch, branch, or switch"),
    )

    result = CLI._version_command(SimpleNamespace(root=tmp_path), ["use", "1.1.9", "--dry-run"])

    assert result == 0
    assert "cambiar el checkout a v1.1.9" in capsys.readouterr().out


def test_version_switch_refuses_a_dirty_worktree_before_docker_check(tmp_path: Path, monkeypatch, capsys):
    calls: list[tuple[str, ...]] = []

    def fake_git(_root: Path, *args: str):
        calls.append(args)
        if args == ("rev-parse", "--is-inside-work-tree"):
            return subprocess.CompletedProcess(["git"], 0, "true\n", "")
        if args == ("status", "--porcelain", "--untracked-files=normal"):
            return subprocess.CompletedProcess(["git"], 0, " M README.md\n", "")
        return subprocess.CompletedProcess(["git"], 1, "", "unexpected git call")

    monkeypatch.setattr(CLI, "_git_result", fake_git)

    assert CLI._version_switch_preflight(tmp_path) is False
    assert calls == [
        ("rev-parse", "--is-inside-work-tree"),
        ("status", "--porcelain", "--untracked-files=normal"),
    ]
    assert "cambios locales" in capsys.readouterr().err


def test_uninstall_all_dry_run_does_not_call_docker_or_stop_scripts(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setattr(CLI.subprocess, "run", lambda *_args, **_kwargs: pytest.fail("dry-run must be read-only"))

    result = CLI._uninstall_command(SimpleNamespace(root=tmp_path), ["--scope", "all", "--dry-run"])

    output = capsys.readouterr().out
    assert result == 0
    assert "Plan: detener de forma ordenada el perfil 5g-nsa-x310" in output
    assert "Plan: detener el stack web/monitorizacion" in output
    assert "No se hicieron cambios." in output


def test_uninstall_purge_dry_run_lists_only_labeled_volumes(tmp_path: Path, monkeypatch, capsys):
    expected = ["lain5g-lab-5g-sa_mongo-data"]
    monkeypatch.setattr(CLI, "_project_volumes", lambda _projects: (expected, None))
    monkeypatch.setattr(CLI.subprocess, "run", lambda *_args, **_kwargs: pytest.fail("dry-run must not mutate Docker"))

    result = CLI._uninstall_command(
        SimpleNamespace(root=tmp_path), ["--scope", "5g-sa", "--purge-data", "--dry-run"]
    )

    output = capsys.readouterr().out
    assert result == 0
    assert expected[0] in output
    assert "No se hicieron cambios." in output


def test_uninstall_purge_requires_interactive_confirmation(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setattr(CLI, "_project_volumes", lambda _projects: (["subscriber-data"], None))
    monkeypatch.setattr(CLI.sys, "stdin", SimpleNamespace(isatty=lambda: False))
    monkeypatch.setattr(CLI.subprocess, "run", lambda *_args, **_kwargs: pytest.fail("must refuse before Docker mutation"))

    result = CLI._uninstall_command(
        SimpleNamespace(root=tmp_path), ["--scope", "5g-sa", "--purge-data", "--yes"]
    )

    assert result == 2
    assert "terminal interactiva" in capsys.readouterr().err


def _complete_checkout(tmp_path: Path) -> Path:
    checkout = tmp_path / "Lain5G"
    checkout.mkdir(parents=True)
    (checkout / ".git").mkdir()
    (checkout / "lain5g").write_text("#!/usr/bin/env python3\n", encoding="utf-8")
    (checkout / "VERSION").write_text("1.1.8\n", encoding="utf-8")
    (checkout / "docker-compose.app.yml").write_text("services: {}\n", encoding="utf-8")
    return checkout


def test_complete_uninstall_dry_run_previews_checkout_and_data_without_mutation(tmp_path: Path, monkeypatch, capsys):
    checkout = _complete_checkout(tmp_path)
    state_dir = tmp_path / "state" / "lain5g"
    state_dir.mkdir(parents=True)
    monkeypatch.setenv("XDG_STATE_HOME", str(state_dir.parent))
    monkeypatch.setattr(CLI, "_project_volumes", lambda _projects: (["lain5g-data"], None))
    monkeypatch.setattr(CLI, "_project_images", lambda: (["lain5g-lab/open5gs:local"], None))
    monkeypatch.setattr(CLI.subprocess, "run", lambda *_args, **_kwargs: pytest.fail("dry-run must not mutate Docker"))

    result = CLI._uninstall_command(
        SimpleNamespace(root=checkout), ["--scope", "all", "--purge-all", "--dry-run"]
    )

    output = capsys.readouterr().out
    assert result == 0
    assert str(checkout) in output
    assert "lain5g-data" in output
    assert "lain5g-lab/open5gs:local" in output
    assert "Plan: borrar todos los volumenes OpenLain5G" in output
    assert checkout.exists() and state_dir.exists()


def test_complete_uninstall_cannot_be_approved_noninteractively_even_with_yes(tmp_path: Path, monkeypatch, capsys):
    checkout = _complete_checkout(tmp_path)
    monkeypatch.setattr(CLI, "_project_volumes", lambda _projects: ([], None))
    monkeypatch.setattr(CLI, "_project_images", lambda: ([], None))
    monkeypatch.setattr(CLI.sys, "stdin", SimpleNamespace(isatty=lambda: False))
    monkeypatch.setattr(CLI.subprocess, "run", lambda *_args, **_kwargs: pytest.fail("must refuse before Docker mutation"))

    result = CLI._uninstall_command(
        SimpleNamespace(root=checkout), ["--scope", "all", "--purge-all", "--yes"]
    )

    assert result == 2
    assert checkout.exists()
    assert "--yes no omite" in capsys.readouterr().err


def test_complete_uninstall_requires_the_exact_phrase_before_docker_mutation(tmp_path: Path, monkeypatch, capsys):
    checkout = _complete_checkout(tmp_path)
    monkeypatch.setattr(CLI, "_project_volumes", lambda _projects: ([], None))
    monkeypatch.setattr(CLI, "_project_images", lambda: ([], None))
    monkeypatch.setattr(CLI.sys, "stdin", SimpleNamespace(isatty=lambda: True))
    monkeypatch.setattr(CLI, "_input", lambda _prompt: "yes")
    monkeypatch.setattr(CLI.subprocess, "run", lambda *_args, **_kwargs: pytest.fail("wrong phrase must refuse before Docker"))

    result = CLI._uninstall_command(
        SimpleNamespace(root=checkout), ["--scope", "all", "--purge-all"]
    )

    assert result == 1
    assert checkout.exists()
    assert "no se borro el codigo ni los datos" in capsys.readouterr().out


def test_complete_uninstall_rejects_a_state_directory_that_contains_the_checkout(tmp_path: Path, monkeypatch):
    state_root = tmp_path / "state"
    checkout = _complete_checkout(state_root / "lain5g")
    monkeypatch.setenv("XDG_STATE_HOME", str(state_root))

    state, _logs, error = CLI._complete_uninstall_paths(checkout)

    assert state is None
    assert "demasiado amplia" in (error or "")


def test_complete_uninstall_requires_all_scope(tmp_path: Path, capsys):
    result = CLI._uninstall_command(SimpleNamespace(root=tmp_path), ["--scope", "app", "--purge-all"])

    assert result == 2
    assert "requiere el alcance all" in capsys.readouterr().err


def test_uninstall_refuses_rf_active_marker_without_stopping_anything(tmp_path: Path, monkeypatch, capsys):
    marker = tmp_path / CLI.RF_ACTIVE_MARKERS[0]
    marker.parent.mkdir(parents=True)
    marker.write_text("active\n", encoding="utf-8")
    monkeypatch.setattr(CLI.subprocess, "run", lambda *_args, **_kwargs: pytest.fail("must stop before Docker"))

    result = CLI._uninstall_command(SimpleNamespace(root=tmp_path), ["--scope", "all", "--yes"])

    assert result == 1
    assert "Emergency Stop" in capsys.readouterr().err
