from __future__ import annotations

import shlex
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest

from ai.backend.kernel.intrinsic import prepare_ttyd_service


class TestPrepareTtydService:
    """Tests for prepare_ttyd_service() building the etty command line."""

    @pytest.fixture
    def bash_only(self) -> Generator[None, None, None]:
        with patch.object(Path, "exists", lambda self: str(self) == "/bin/bash"):
            yield

    @pytest.fixture
    def ash_only(self) -> Generator[None, None, None]:
        with patch.object(Path, "exists", lambda self: str(self) == "/bin/ash"):
            yield

    async def test_shell_script_survives_etty_command_parsing(self, bash_only: None) -> None:
        cmdargs, _env = await prepare_ttyd_service({"port": 7681})

        assert cmdargs[0] == "/opt/kernel/etty"
        assert cmdargs[cmdargs.index("--bind") + 1] == "0.0.0.0"
        assert cmdargs[cmdargs.index("-p") + 1] == "7681"
        command = cmdargs[cmdargs.index("--command") + 1]
        assert shlex.split(command) == [
            "/bin/bash",
            "-c",
            "export SHELL=/bin/bash; /opt/kernel/tmux -2 attach",
        ]

    async def test_ash_runs_without_tmux(self, ash_only: None) -> None:
        cmdargs, _env = await prepare_ttyd_service({"port": 7681})

        assert cmdargs[cmdargs.index("--command") + 1] == "/bin/ash"
