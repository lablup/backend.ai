from __future__ import annotations

import os
import signal
from collections.abc import Callable
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.account_manager import server
from ai.backend.common.process.child_exit import ChildStatus


@pytest.fixture
def loop() -> MagicMock:
    return MagicMock()


@pytest.fixture
def child_status() -> ChildStatus:
    return ChildStatus()


@pytest.fixture
def stub_server(monkeypatch: pytest.MonkeyPatch) -> Callable[[Exception | None], AsyncMock]:
    def stub(setup_error: Exception | None) -> AsyncMock:
        root_ctx = MagicMock()
        root_ctx.local_config.account_manager.ssl_enabled = False
        runner = AsyncMock()
        runner.setup.side_effect = setup_error
        monkeypatch.setattr(server, "build_root_app", lambda *_, **__: {"_root.context": root_ctx})
        monkeypatch.setattr(server, "build_internal_app", MagicMock())
        monkeypatch.setattr(server, "Profiler", MagicMock())
        monkeypatch.setattr("aiomonitor.Monitor", MagicMock())
        monkeypatch.setattr("aiohttp.web.AppRunner", MagicMock(return_value=runner))
        monkeypatch.setattr("aiohttp.web.TCPSite", lambda *_, **__: AsyncMock())
        monkeypatch.setattr(os, "geteuid", lambda: 1000)
        return runner

    return stub


async def _run_server_main(loop: MagicMock, child_status: ChildStatus) -> list[str]:
    reached: list[str] = []
    args: tuple[Any, ...] = (None, None, (child_status,))
    async with server.server_main(loop, 0, args):
        reached.append("serving")
    return reached


class TestServerMainInitFailure:
    async def test_a_failed_initialization_signals_the_process_group(
        self,
        loop: MagicMock,
        child_status: ChildStatus,
        stub_server: Callable[[Exception | None], AsyncMock],
    ) -> None:
        runner = stub_server(RuntimeError("cannot bind"))

        # The worker still reaches its serving point, so aiotools runs its shutdown routines.
        assert await _run_server_main(loop, child_status) == ["serving"]

        assert child_status.init_failed.is_set()
        loop.call_later.assert_called_once_with(0.2, os.kill, 0, signal.SIGINT)
        runner.cleanup.assert_awaited_once()

    async def test_a_successful_initialization_leaves_the_process_group_alone(
        self,
        loop: MagicMock,
        child_status: ChildStatus,
        stub_server: Callable[[Exception | None], AsyncMock],
    ) -> None:
        stub_server(None)

        assert await _run_server_main(loop, child_status) == ["serving"]

        assert not child_status.init_failed.is_set()
        loop.call_later.assert_not_called()
