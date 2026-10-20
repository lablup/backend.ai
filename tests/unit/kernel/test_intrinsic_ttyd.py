from __future__ import annotations

import shlex
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest

from ai.backend.kernel.intrinsic import prepare_etty_service, prepare_ttyd_service

_BASH_TMUX = ["/bin/bash", "-c", "export SHELL=/bin/bash; /opt/kernel/tmux -2 attach"]


@pytest.fixture
def bash_only() -> Generator[None, None, None]:
    with patch.object(Path, "exists", lambda self: str(self) == "/bin/bash"):
        yield


@pytest.fixture
def ash_only() -> Generator[None, None, None]:
    with patch.object(Path, "exists", lambda self: str(self) == "/bin/ash"):
        yield


class TestPrepareTtydService:
    async def test_passes_shell_as_positional_arguments(self, bash_only: None) -> None:
        cmdargs, _env = await prepare_ttyd_service({"port": 7681})

        assert cmdargs == ["/opt/kernel/ttyd", "-W", "-p", "7681", *_BASH_TMUX]


class TestPrepareEttyService:
    async def test_shell_script_survives_etty_command_parsing(self, bash_only: None) -> None:
        cmdargs, _env = await prepare_etty_service({"port": 7682})

        assert cmdargs[0] == "/opt/kernel/etty"
        assert cmdargs[cmdargs.index("--bind") + 1] == "0.0.0.0"
        assert cmdargs[cmdargs.index("-p") + 1] == "7682"
        assert shlex.split(cmdargs[cmdargs.index("--command") + 1]) == _BASH_TMUX

    async def test_ash_runs_without_tmux(self, ash_only: None) -> None:
        cmdargs, _env = await prepare_etty_service({"port": 7682})

        assert cmdargs[cmdargs.index("--command") + 1] == "/bin/ash"
