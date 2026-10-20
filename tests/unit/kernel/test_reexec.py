from __future__ import annotations

import os
import site
import sys
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai.backend.kernel import _reexec_with_argv0

VENV = "/opt/some-venv"


@pytest.fixture
def mock_execvpe() -> Iterator[MagicMock]:
    with (
        patch("os.execvpe") as mock_exec,
        patch.object(Path, "write_text"),
    ):
        yield mock_exec


@pytest.fixture
def stage1(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BACKEND_REEXECED", raising=False)
    monkeypatch.delenv("PYTHONHOME", raising=False)


@pytest.fixture
def stage2(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BACKEND_REEXECED", "1")
    monkeypatch.setenv("PYTHONHOME", sys.base_prefix)
    monkeypatch.setattr(sys, "prefix", sys.prefix)
    monkeypatch.setattr(sys, "path", list(sys.path))


@pytest.fixture
def no_virtual_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VIRTUAL_ENV", raising=False)


@pytest.fixture
def with_virtual_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VIRTUAL_ENV", VENV)


class TestReexecStage1:
    @pytest.mark.usefixtures("stage1", "no_virtual_env")
    def test_sets_pythonhome_without_virtual_env(self, mock_execvpe: MagicMock) -> None:
        _reexec_with_argv0("bai-krunner")
        _, argv, env = mock_execvpe.call_args.args
        assert argv[0] == "bai-krunner"
        assert env["BACKEND_REEXECED"] == "1"
        assert env["PYTHONHOME"] == sys.base_prefix

    @pytest.mark.usefixtures("stage1", "with_virtual_env")
    def test_sets_pythonhome_with_virtual_env(self, mock_execvpe: MagicMock) -> None:
        _reexec_with_argv0("bai-krunner")
        _, _, env = mock_execvpe.call_args.args
        assert env["PYTHONHOME"] == sys.base_prefix
        assert env["VIRTUAL_ENV"] == VENV


class TestReexecStage2:
    @pytest.mark.usefixtures("stage2", "no_virtual_env")
    def test_removes_pythonhome(self) -> None:
        _reexec_with_argv0("bai-krunner")
        assert "PYTHONHOME" not in os.environ

    @pytest.mark.usefixtures("stage2", "with_virtual_env")
    def test_adds_venv_site_packages(self) -> None:
        _reexec_with_argv0("bai-krunner")
        assert "PYTHONHOME" not in os.environ
        assert sys.prefix == VENV
        assert sys.path[0] == site.getsitepackages([VENV])[0]
