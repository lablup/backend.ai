from __future__ import annotations

import asyncio
import os
from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock, patch

import aiomonitor
import pytest
from aiohttp import web

from ai.backend.appproxy.worker import server


@pytest.fixture
def monitor_start() -> Iterator[MagicMock]:
    with (
        patch.object(aiomonitor.Monitor, "start", autospec=True) as start,
        patch.object(aiomonitor.Monitor, "close", autospec=True),
    ):
        yield start


@pytest.fixture
def webapp_stubs() -> Iterator[None]:
    with (
        patch.object(server, "build_root_app", MagicMock()),
        patch.object(web, "AppRunner", return_value=AsyncMock()),
        patch.object(web, "TCPSite", return_value=AsyncMock()),
        patch.object(os, "geteuid", return_value=1000),
    ):
        yield


@pytest.mark.usefixtures("webapp_stubs")
async def test_server_main_opens_aiomonitor_on_localhost(monitor_start: MagicMock) -> None:
    local_config = MagicMock()
    local_config.debug.enhanced_aiomonitor_task_info = False
    local_config.proxy_worker.tls_listen = False
    local_config.proxy_worker.aiomonitor_termui_port = 48600
    local_config.proxy_worker.aiomonitor_webui_port = 49600

    async with server.server_main(asyncio.get_running_loop(), 0, [local_config]):
        pass

    monitor_start.assert_called_once()
    monitor: aiomonitor.Monitor = monitor_start.call_args.args[0]
    assert monitor.host == "127.0.0.1"
