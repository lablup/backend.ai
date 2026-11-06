from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_mock

from ai.backend.appproxy.worker.proxy.frontend.h2.port import PortFrontend

_BIND_HOST = "192.0.2.1"
_LISTEN_PORT = 10200
_API_PORT = 20000


class TestStart:
    @pytest.fixture
    async def nghttpx_exec_of_started_no_tls_frontend(
        self, mocker: pytest_mock.MockerFixture
    ) -> AsyncIterator[AsyncMock]:
        root_context = MagicMock()
        worker_config = root_context.local_config.proxy_worker
        worker_config.tls_listen = False
        worker_config.http2.api_port_pool = (_API_PORT, _API_PORT)
        worker_config.port_proxy.bind_host = _BIND_HOST
        worker_config.port_proxy.bind_port_range = (_LISTEN_PORT, _LISTEN_PORT)
        nghttpx_stream = MagicMock(readline=AsyncMock(return_value=b""))
        create_subprocess_exec = mocker.patch(
            "ai.backend.appproxy.worker.proxy.frontend.h2.port.subprocess.create_subprocess_exec",
            AsyncMock(
                return_value=MagicMock(
                    stdout=nghttpx_stream, stderr=nghttpx_stream, wait=AsyncMock()
                )
            ),
        )
        frontend = PortFrontend(root_context)
        frontend.proc_monitor_tasks = []
        frontend.log_monitor_tasks = []
        await frontend.start()
        yield create_subprocess_exec
        await asyncio.gather(*frontend.proc_monitor_tasks, *frontend.log_monitor_tasks)

    async def test_nghttpx_listens_on_the_bind_host_without_tls(
        self, nghttpx_exec_of_started_no_tls_frontend: AsyncMock
    ) -> None:
        assert (
            f"--frontend={_BIND_HOST},{_LISTEN_PORT};no-tls"
            in nghttpx_exec_of_started_no_tls_frontend.call_args.args
        )
