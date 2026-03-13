from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.session.request import (
    CommitSessionRequest,
    ExecuteRequest,
    GetContainerLogsRequest,
    StartServiceRequest,
)
from ai.backend.common.dto.manager.session.response import (
    CommitSessionResponse,
    ExecuteResponse,
    GetContainerLogsResponse,
    StartServiceResponse,
)
from ai.backend.manager.models.kernel import kernels
from ai.backend.manager.models.scaling_group import scaling_groups

from .conftest import SessionSeedData


class TestSessionExecute:
    """SDK execute() — mode='query' code execution returns console output."""

    async def test_execute_query_mode_returns_console_output(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        agent_registry: AsyncMock,
    ) -> None:
        agent_registry.increment_session_usage.return_value = None
        agent_registry.execute.return_value = {
            "status": "finished",
            "runId": "test-run-id",
            "exitCode": 0,
            "console": [["stdout", "Hello World\n"]],
            "options": None,
            "files": [],
        }

        result = await admin_registry.session.execute(
            session_seed.session_name,
            ExecuteRequest(mode="query", code='print("Hello World")', run_id="test-run-id"),
        )
        assert isinstance(result, ExecuteResponse)
        assert result.root["result"]["status"] == "finished"
        assert result.root["result"]["runId"] == "test-run-id"
        assert result.root["result"]["exitCode"] == 0


class TestSessionCommit:
    """SDK commit() — no-arg call commits with filename=None."""

    async def test_commit_with_no_filename(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        agent_registry: AsyncMock,
    ) -> None:
        agent_registry.commit_session_to_file.return_value = {
            "bgtask_id": str(uuid.uuid4()),
        }

        result = await admin_registry.session.commit(
            session_seed.session_name,
            CommitSessionRequest(),
        )
        assert isinstance(result, CommitSessionResponse)
        assert "bgtask_id" in result.root

        agent_registry.commit_session_to_file.assert_called_once()
        call_args = agent_registry.commit_session_to_file.call_args
        assert call_args[0][1] is None  # filename=None


class TestSessionRestart:
    """SDK restart() — session restart succeeds."""

    async def test_restart_succeeds(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        agent_registry: AsyncMock,
    ) -> None:
        agent_registry.increment_session_usage.return_value = None
        agent_registry.restart_session.return_value = None

        await admin_registry.session.restart(session_seed.session_name)

        agent_registry.restart_session.assert_called_once()


class TestSessionGetLogs:
    """SDK get_logs() — container log retrieval."""

    async def test_get_logs_no_kernel_id_returns_main_kernel_log(
        self,
        admin_registry: BackendAIClientRegistry,
        terminated_session_seed: SessionSeedData,
    ) -> None:
        """Terminated session reads logs from database without agent RPC."""
        result = await admin_registry.session.get_container_logs(
            terminated_session_seed.session_name,
        )
        assert isinstance(result, GetContainerLogsResponse)
        assert result.root["result"]["logs"] == "Hello from terminated container\n"

    async def test_get_logs_with_specific_kernel_id(
        self,
        admin_registry: BackendAIClientRegistry,
        terminated_session_seed: SessionSeedData,
    ) -> None:
        """Specific kernel_id returns that kernel's log."""
        result = await admin_registry.session.get_container_logs(
            terminated_session_seed.session_name,
            GetContainerLogsRequest(kernel_id=terminated_session_seed.kernel_id),
        )
        assert isinstance(result, GetContainerLogsResponse)
        assert result.root["result"]["logs"] == "Hello from terminated container\n"

    async def test_get_logs_from_running_session_calls_agent(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        agent_registry: AsyncMock,
    ) -> None:
        """Running session fetches logs from agent."""
        agent_registry.increment_session_usage.return_value = None
        agent_registry.get_logs_from_agent.return_value = "live container log output\n"

        result = await admin_registry.session.get_container_logs(
            session_seed.session_name,
        )
        assert isinstance(result, GetContainerLogsResponse)
        assert result.root["result"]["logs"] == "live container log output\n"
        agent_registry.get_logs_from_agent.assert_called_once()


class TestSessionStartService:
    """SDK start_service() — app name returns service token/wsproxy address."""

    async def test_start_service_returns_token_and_wsproxy(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        db_engine: SAEngine,
        scaling_group_fixture: str,
        agent_registry: AsyncMock,
        appproxy_client_pool: AsyncMock,
    ) -> None:
        wsproxy_addr = "http://127.0.0.1:5050"

        # Set wsproxy_addr on scaling group
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.update(scaling_groups)
                .where(scaling_groups.c.name == scaling_group_fixture)
                .values(wsproxy_addr=wsproxy_addr)
            )

        # Add service_ports and agent_addr to the kernel
        service_ports = [
            {
                "name": "ttyd",
                "protocol": "http",
                "container_ports": [8080],
                "host_ports": [30080],
                "host_port": 30080,
                "is_inference": False,
            }
        ]
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.update(kernels)
                .where(kernels.c.id == session_seed.kernel_id)
                .values(
                    service_ports=service_ports,
                    agent_addr="tcp://127.0.0.1:6001",
                    kernel_host="127.0.0.1",
                )
            )

        # Mock appproxy client
        mock_status = MagicMock()
        mock_status.advertise_address = wsproxy_addr
        mock_client = AsyncMock()
        mock_client.fetch_status.return_value = mock_status
        appproxy_client_pool.load_client.return_value = mock_client

        # Mock agent start_service
        agent_registry.increment_session_usage.return_value = None
        agent_registry.start_service.return_value = {"status": "started"}

        # Mock the HTTP POST to wsproxy /v2/conf
        mock_resp = AsyncMock()
        mock_resp.json.return_value = {"token": "test-token-xyz"}
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_session_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_session_obj = MagicMock()
        mock_session_obj.post.return_value = mock_session_ctx
        mock_session_cls = AsyncMock()
        mock_session_cls.__aenter__ = AsyncMock(return_value=mock_session_obj)
        mock_session_cls.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession", return_value=mock_session_cls):
            result = await admin_registry.session.start_service(
                session_seed.session_name,
                StartServiceRequest(app="ttyd"),
            )

        assert isinstance(result, StartServiceResponse)
        assert result.token == "test-token-xyz"
        assert result.wsproxy_addr == wsproxy_addr
