from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.exceptions import InvalidRequestError, NotFoundError, ServerError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.session.request import (
    CompleteRequest,
    ExecuteRequest,
    ShutdownServiceRequest,
    StartServiceRequest,
)
from ai.backend.common.dto.manager.session.response import (
    CompleteResponse,
    ExecuteResponse,
    StartServiceResponse,
)
from ai.backend.manager.models.kernel import kernels
from ai.backend.manager.models.scaling_group import scaling_groups
from ai.backend.manager.models.session.row import SessionRow

from .conftest import SessionSeedData

_WSPROXY_ADDR = "http://127.0.0.1:5050"
_SERVICE_PORTS_TTYD = [
    {
        "name": "ttyd",
        "protocol": "http",
        "container_ports": [8080],
        "host_ports": [30080],
        "host_port": 30080,
        "is_inference": False,
    }
]


def _make_wsproxy_mock(token: str = "test-token-xyz") -> AsyncMock:
    """Create a mock for aiohttp.ClientSession returning a wsproxy token."""
    mock_resp = AsyncMock()
    mock_resp.json.return_value = {"token": token}
    mock_session_ctx = AsyncMock()
    mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_session_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_session_obj = MagicMock()
    mock_session_obj.post.return_value = mock_session_ctx
    mock_session_cls = AsyncMock()
    mock_session_cls.__aenter__ = AsyncMock(return_value=mock_session_obj)
    mock_session_cls.__aexit__ = AsyncMock(return_value=False)
    return mock_session_cls


# ---------------------------------------------------------------------------
# Execute endpoint — query mode, auto run_id, code=None
# ---------------------------------------------------------------------------


class TestSessionExecuteQuery:
    """Execute endpoint — query mode, auto run_id, and code=None."""

    async def test_execute_query_mode(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        agent_registry: AsyncMock,
    ) -> None:
        """S-1: mode='query', code, run_id → ExecuteResponse with result keys."""
        agent_registry.increment_session_usage.return_value = None
        agent_registry.execute.return_value = {
            "status": "finished",
            "runId": "abc",
            "exitCode": 0,
            "console": [["stdout", "hello\n"]],
            "options": None,
            "files": [],
        }

        result = await admin_registry.session.execute(
            session_seed.session_name,
            ExecuteRequest(mode="query", code="print('hello')", run_id="abc"),
        )

        assert isinstance(result, ExecuteResponse)
        assert result.root["result"]["status"] == "finished"
        assert result.root["result"]["runId"] == "abc"
        assert result.root["result"]["exitCode"] == 0
        assert "console" in result.root["result"]

    async def test_execute_with_no_run_id(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        agent_registry: AsyncMock,
    ) -> None:
        """S-2: run_id=None in v2 mode with non-continue mode — execute still called."""
        agent_registry.increment_session_usage.return_value = None
        agent_registry.execute.return_value = {
            "status": "finished",
            "runId": None,
            "exitCode": 0,
            "console": [],
            "options": None,
            "files": [],
        }

        result = await admin_registry.session.execute(
            session_seed.session_name,
            ExecuteRequest(mode="query", code="print('hello')"),
        )

        assert isinstance(result, ExecuteResponse)
        agent_registry.execute.assert_called_once()

    async def test_execute_with_code_none(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        agent_registry: AsyncMock,
    ) -> None:
        """S-7: code=None → agent called with code='' (empty string)."""
        agent_registry.increment_session_usage.return_value = None
        agent_registry.execute.return_value = {
            "status": "finished",
            "runId": "abc",
            "exitCode": 0,
            "console": [],
            "options": None,
            "files": [],
        }

        result = await admin_registry.session.execute(
            session_seed.session_name,
            ExecuteRequest(mode="query", run_id="abc", code=None),
        )

        assert isinstance(result, ExecuteResponse)
        call_args = agent_registry.execute.call_args
        # positional args: (session, api_version, run_id, mode, code, opts)
        assert call_args[0][4] == ""


# ---------------------------------------------------------------------------
# Execute endpoint — batch and complete mode
# ---------------------------------------------------------------------------


class TestSessionExecuteModes:
    """Execute endpoint — batch and complete mode."""

    async def test_execute_batch_mode(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        agent_registry: AsyncMock,
    ) -> None:
        """S-3: mode='batch' → agent_registry.execute called with mode='batch'."""
        agent_registry.increment_session_usage.return_value = None
        agent_registry.execute.return_value = {
            "status": "finished",
            "runId": "batch-run-1",
            "exitCode": 0,
            "console": [],
            "options": None,
            "files": [],
        }

        result = await admin_registry.session.execute(
            session_seed.session_name,
            ExecuteRequest(mode="batch", code="x = 1", run_id="batch-run-1"),
        )

        assert isinstance(result, ExecuteResponse)
        call_args = agent_registry.execute.call_args
        # positional args: (session, api_version, run_id, mode, code, opts)
        assert call_args[0][3] == "batch"

    async def test_execute_complete_mode_calls_get_completions(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        agent_registry: AsyncMock,
    ) -> None:
        """S-6: mode='complete' → get_completions called instead of execute."""
        agent_registry.increment_session_usage.return_value = None
        mock_completion = MagicMock()
        mock_completion.as_dict.return_value = {"completions": ["os.path", "os.getcwd"]}
        agent_registry.get_completions.return_value = mock_completion

        result = await admin_registry.session.execute(
            session_seed.session_name,
            ExecuteRequest(mode="complete", code="os."),
        )

        assert isinstance(result, ExecuteResponse)
        agent_registry.get_completions.assert_called_once()
        agent_registry.execute.assert_not_called()


# ---------------------------------------------------------------------------
# Execute endpoint — validation and not-found failures
# ---------------------------------------------------------------------------


class TestSessionExecuteFailures:
    """Execute endpoint — validation and not-found failures."""

    async def test_execute_continue_without_run_id(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        """F-BIZ-1: mode='continue', run_id=None → error (requires run_id)."""
        with pytest.raises(ServerError):
            await admin_registry.session.execute(
                session_seed.session_name,
                ExecuteRequest(mode="continue"),
            )

    async def test_execute_invalid_mode(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        """F-BIZ-2: mode='invalid' → error."""
        with pytest.raises(ServerError):
            await admin_registry.session.execute(
                session_seed.session_name,
                ExecuteRequest(mode="invalid", run_id="r1"),
            )

    async def test_execute_no_mode_in_v2(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        """F-BIZ-3: mode=None in v2 API → error (mode is required)."""
        with pytest.raises(ServerError):
            await admin_registry.session.execute(
                session_seed.session_name,
                ExecuteRequest(mode=None),
            )

    async def test_execute_nonexistent_session(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """F-BIZ-4: Execute on nonexistent session → NotFoundError."""
        with pytest.raises(NotFoundError):
            await admin_registry.session.execute(
                "nonexistent-session-xyz-99999",
                ExecuteRequest(mode="query", code="print('hi')", run_id="r1"),
            )


# ---------------------------------------------------------------------------
# Interrupt endpoint
# ---------------------------------------------------------------------------


class TestSessionInterrupt:
    """Interrupt endpoint."""

    async def test_interrupt_running_session(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        agent_registry: AsyncMock,
    ) -> None:
        """S-8: Interrupt running session → success, agent_registry.interrupt_session called."""
        agent_registry.increment_session_usage.return_value = None
        agent_registry.interrupt_session.return_value = None

        await admin_registry.session.interrupt(session_seed.session_name)

        agent_registry.interrupt_session.assert_called_once()

    async def test_interrupt_nonexistent_session(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """F-BIZ-5: Interrupt nonexistent session → NotFoundError."""
        with pytest.raises(NotFoundError):
            await admin_registry.session.interrupt("nonexistent-session-xyz-99999")


# ---------------------------------------------------------------------------
# Complete endpoint (POST /{session_name}/complete)
# ---------------------------------------------------------------------------


class TestSessionComplete:
    """Complete endpoint (POST /{session_name}/complete)."""

    async def test_complete_returns_completions(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        agent_registry: AsyncMock,
    ) -> None:
        """S-9: code='impo' → CompleteResponse, agent_registry.get_completions called."""
        agent_registry.increment_session_usage.return_value = None
        mock_completion = MagicMock()
        mock_completion.as_dict.return_value = {"completions": ["import os", "import sys"]}
        agent_registry.get_completions.return_value = mock_completion

        result = await admin_registry.session.complete(
            session_seed.session_name,
            CompleteRequest(code="impo"),
        )

        assert isinstance(result, CompleteResponse)
        agent_registry.get_completions.assert_called_once()

    async def test_complete_nonexistent_session(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """F-BIZ-6: Complete on nonexistent session → NotFoundError."""
        with pytest.raises(NotFoundError):
            await admin_registry.session.complete(
                "nonexistent-session-xyz-99999",
                CompleteRequest(code="impo"),
            )


# ---------------------------------------------------------------------------
# Start service endpoint
# ---------------------------------------------------------------------------


class TestSessionStartService:
    """Start service endpoint — app token and wsproxy address scenarios."""

    async def test_start_service_returns_token_and_wsproxy(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        db_engine: SAEngine,
        scaling_group_fixture: str,
        agent_registry: AsyncMock,
        appproxy_client_pool: AsyncMock,
    ) -> None:
        """S-1: Start service 'ttyd' → StartServiceResponse with token and wsproxy_addr."""
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.update(scaling_groups)
                .where(scaling_groups.c.name == scaling_group_fixture)
                .values(wsproxy_addr=_WSPROXY_ADDR)
            )
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.update(kernels)
                .where(kernels.c.id == session_seed.kernel_id)
                .values(
                    service_ports=_SERVICE_PORTS_TTYD,
                    agent_addr="tcp://127.0.0.1:6001",
                    kernel_host="127.0.0.1",
                )
            )

        mock_status = MagicMock()
        mock_status.advertise_address = _WSPROXY_ADDR
        mock_client = AsyncMock()
        mock_client.fetch_status.return_value = mock_status
        appproxy_client_pool.load_client.return_value = mock_client

        agent_registry.increment_session_usage.return_value = None
        agent_registry.start_service.return_value = {"status": "started"}

        mock_session_cls = _make_wsproxy_mock(token="test-token-xyz")

        with patch(
            "ai.backend.manager.services.session.service.aiohttp.ClientSession",
            return_value=mock_session_cls,
        ):
            result = await admin_registry.session.start_service(
                session_seed.session_name,
                StartServiceRequest(app="ttyd"),
            )

        assert isinstance(result, StartServiceResponse)
        assert result.token == "test-token-xyz"
        assert result.wsproxy_addr == _WSPROXY_ADDR

    async def test_start_service_with_specific_port(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        db_engine: SAEngine,
        scaling_group_fixture: str,
        agent_registry: AsyncMock,
        appproxy_client_pool: AsyncMock,
    ) -> None:
        """S-2: Start service with port=8888 → correct host_port used."""
        service_ports = [
            {
                "name": "ttyd",
                "protocol": "http",
                "container_ports": [8080, 8888],
                "host_ports": [30080, 30888],
                "host_port": 30080,
                "is_inference": False,
            }
        ]
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.update(scaling_groups)
                .where(scaling_groups.c.name == scaling_group_fixture)
                .values(wsproxy_addr=_WSPROXY_ADDR)
            )
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

        mock_status = MagicMock()
        mock_status.advertise_address = _WSPROXY_ADDR
        mock_client = AsyncMock()
        mock_client.fetch_status.return_value = mock_status
        appproxy_client_pool.load_client.return_value = mock_client

        agent_registry.increment_session_usage.return_value = None
        agent_registry.start_service.return_value = {"status": "started"}

        mock_session_cls = _make_wsproxy_mock(token="port-test-token")
        with patch(
            "ai.backend.manager.services.session.service.aiohttp.ClientSession",
            return_value=mock_session_cls,
        ):
            result = await admin_registry.session.start_service(
                session_seed.session_name,
                StartServiceRequest(app="ttyd", port=8888),
            )

        assert isinstance(result, StartServiceResponse)
        assert result.token == "port-test-token"

    async def test_start_service_with_arguments_and_envs(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        db_engine: SAEngine,
        scaling_group_fixture: str,
        agent_registry: AsyncMock,
        appproxy_client_pool: AsyncMock,
    ) -> None:
        """S-3: Start service with arguments/envs → opts contain parsed arguments and envs."""
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.update(scaling_groups)
                .where(scaling_groups.c.name == scaling_group_fixture)
                .values(wsproxy_addr=_WSPROXY_ADDR)
            )
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.update(kernels)
                .where(kernels.c.id == session_seed.kernel_id)
                .values(
                    service_ports=_SERVICE_PORTS_TTYD,
                    agent_addr="tcp://127.0.0.1:6001",
                    kernel_host="127.0.0.1",
                )
            )

        mock_status = MagicMock()
        mock_status.advertise_address = _WSPROXY_ADDR
        mock_client = AsyncMock()
        mock_client.fetch_status.return_value = mock_status
        appproxy_client_pool.load_client.return_value = mock_client

        agent_registry.increment_session_usage.return_value = None
        agent_registry.start_service.return_value = {"status": "started"}

        mock_session_cls = _make_wsproxy_mock(token="args-test-token")
        with patch(
            "ai.backend.manager.services.session.service.aiohttp.ClientSession",
            return_value=mock_session_cls,
        ):
            result = await admin_registry.session.start_service(
                session_seed.session_name,
                StartServiceRequest(
                    app="ttyd",
                    arguments=json.dumps(["--port", "8080"]),
                    envs=json.dumps({"DEBUG": "true"}),
                ),
            )

        assert isinstance(result, StartServiceResponse)
        call_args = agent_registry.start_service.call_args
        # positional args: (session, service, opts)
        opts = call_args[0][2]
        assert "arguments" in opts
        assert "envs" in opts

    async def test_start_service_kernel_host_from_agent_addr(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        db_engine: SAEngine,
        scaling_group_fixture: str,
        agent_registry: AsyncMock,
        appproxy_client_pool: AsyncMock,
    ) -> None:
        """S-4: kernel_host=None → kernel_host extracted from agent_addr hostname."""
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.update(scaling_groups)
                .where(scaling_groups.c.name == scaling_group_fixture)
                .values(wsproxy_addr=_WSPROXY_ADDR)
            )
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.update(kernels)
                .where(kernels.c.id == session_seed.kernel_id)
                .values(
                    service_ports=_SERVICE_PORTS_TTYD,
                    agent_addr="tcp://192.168.1.100:6001",
                    kernel_host=None,
                )
            )

        mock_status = MagicMock()
        mock_status.advertise_address = _WSPROXY_ADDR
        mock_client = AsyncMock()
        mock_client.fetch_status.return_value = mock_status
        appproxy_client_pool.load_client.return_value = mock_client

        agent_registry.increment_session_usage.return_value = None
        agent_registry.start_service.return_value = {"status": "started"}

        mock_resp = AsyncMock()
        mock_resp.json.return_value = {"token": "host-test-token"}
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_session_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_session_obj = MagicMock()
        mock_session_obj.post.return_value = mock_session_ctx
        mock_session_cls = AsyncMock()
        mock_session_cls.__aenter__ = AsyncMock(return_value=mock_session_obj)
        mock_session_cls.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "ai.backend.manager.services.session.service.aiohttp.ClientSession",
            return_value=mock_session_cls,
        ):
            result = await admin_registry.session.start_service(
                session_seed.session_name,
                StartServiceRequest(app="ttyd"),
            )

        assert isinstance(result, StartServiceResponse)
        # Verify kernel_host was extracted from agent_addr
        post_call_kwargs = mock_session_obj.post.call_args[1]
        assert post_call_kwargs["json"]["kernel_host"] == "192.168.1.100"

    async def test_start_service_wsproxy_advertise_address_fallback(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        db_engine: SAEngine,
        scaling_group_fixture: str,
        agent_registry: AsyncMock,
        appproxy_client_pool: AsyncMock,
    ) -> None:
        """S-5: advertise_address=None → fallback to original wsproxy_addr."""
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.update(scaling_groups)
                .where(scaling_groups.c.name == scaling_group_fixture)
                .values(wsproxy_addr=_WSPROXY_ADDR)
            )
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.update(kernels)
                .where(kernels.c.id == session_seed.kernel_id)
                .values(
                    service_ports=_SERVICE_PORTS_TTYD,
                    agent_addr="tcp://127.0.0.1:6001",
                    kernel_host="127.0.0.1",
                )
            )

        mock_status = MagicMock()
        mock_status.advertise_address = None  # No advertise_address
        mock_client = AsyncMock()
        mock_client.fetch_status.return_value = mock_status
        appproxy_client_pool.load_client.return_value = mock_client

        agent_registry.increment_session_usage.return_value = None
        agent_registry.start_service.return_value = {"status": "started"}

        mock_session_cls = _make_wsproxy_mock(token="fallback-test-token")
        with patch(
            "ai.backend.manager.services.session.service.aiohttp.ClientSession",
            return_value=mock_session_cls,
        ):
            result = await admin_registry.session.start_service(
                session_seed.session_name,
                StartServiceRequest(app="ttyd"),
            )

        assert isinstance(result, StartServiceResponse)
        # wsproxy_addr should fall back to the original (not advertise_address)
        assert result.wsproxy_addr == _WSPROXY_ADDR


# ---------------------------------------------------------------------------
# Start service endpoint — failures
# ---------------------------------------------------------------------------


class TestSessionStartServiceFailures:
    """Start service endpoint — failure scenarios."""

    async def test_start_nonexistent_service(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        db_engine: SAEngine,
        scaling_group_fixture: str,
        appproxy_client_pool: AsyncMock,
    ) -> None:
        """F-BIZ-1: Service name not in service_ports → NotFoundError (AppNotFound)."""
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.update(scaling_groups)
                .where(scaling_groups.c.name == scaling_group_fixture)
                .values(wsproxy_addr=_WSPROXY_ADDR)
            )
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.update(kernels)
                .where(kernels.c.id == session_seed.kernel_id)
                .values(
                    service_ports=_SERVICE_PORTS_TTYD,
                    agent_addr="tcp://127.0.0.1:6001",
                    kernel_host="127.0.0.1",
                )
            )

        mock_status = MagicMock()
        mock_status.advertise_address = _WSPROXY_ADDR
        mock_client = AsyncMock()
        mock_client.fetch_status.return_value = mock_status
        appproxy_client_pool.load_client.return_value = mock_client

        with pytest.raises(NotFoundError):
            await admin_registry.session.start_service(
                session_seed.session_name,
                StartServiceRequest(app="nonexistent-app"),
            )

    async def test_start_inference_app_rejected(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        db_engine: SAEngine,
        scaling_group_fixture: str,
        appproxy_client_pool: AsyncMock,
    ) -> None:
        """F-BIZ-2: Inference app → InvalidRequestError."""
        inference_service_ports = [
            {
                "name": "inference-svc",
                "protocol": "http",
                "container_ports": [8080],
                "host_ports": [30080],
                "host_port": 30080,
                "is_inference": True,
            }
        ]
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.update(scaling_groups)
                .where(scaling_groups.c.name == scaling_group_fixture)
                .values(wsproxy_addr=_WSPROXY_ADDR)
            )
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.update(kernels)
                .where(kernels.c.id == session_seed.kernel_id)
                .values(
                    service_ports=inference_service_ports,
                    agent_addr="tcp://127.0.0.1:6001",
                    kernel_host="127.0.0.1",
                )
            )

        mock_status = MagicMock()
        mock_status.advertise_address = _WSPROXY_ADDR
        mock_client = AsyncMock()
        mock_client.fetch_status.return_value = mock_status
        appproxy_client_pool.load_client.return_value = mock_client

        with pytest.raises(InvalidRequestError):
            await admin_registry.session.start_service(
                session_seed.session_name,
                StartServiceRequest(app="inference-svc"),
            )

    async def test_start_with_invalid_port(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        db_engine: SAEngine,
        scaling_group_fixture: str,
        appproxy_client_pool: AsyncMock,
    ) -> None:
        """F-BIZ-3: Port not in container_ports → InvalidRequestError."""
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.update(scaling_groups)
                .where(scaling_groups.c.name == scaling_group_fixture)
                .values(wsproxy_addr=_WSPROXY_ADDR)
            )
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.update(kernels)
                .where(kernels.c.id == session_seed.kernel_id)
                .values(
                    service_ports=_SERVICE_PORTS_TTYD,
                    agent_addr="tcp://127.0.0.1:6001",
                    kernel_host="127.0.0.1",
                )
            )

        mock_status = MagicMock()
        mock_status.advertise_address = _WSPROXY_ADDR
        mock_client = AsyncMock()
        mock_client.fetch_status.return_value = mock_status
        appproxy_client_pool.load_client.return_value = mock_client

        with pytest.raises(InvalidRequestError):
            await admin_registry.session.start_service(
                session_seed.session_name,
                StartServiceRequest(app="ttyd", port=9999),
            )

    async def test_start_with_no_scaling_group(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        db_engine: SAEngine,
    ) -> None:
        """F-BIZ-4: Session has no scaling_group → ServerError (ServiceUnavailable)."""
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.update(SessionRow.__table__)
                .where(SessionRow.__table__.c.id == session_seed.session_id)
                .values(scaling_group_name=None)
            )

        with pytest.raises(ServerError):
            await admin_registry.session.start_service(
                session_seed.session_name,
                StartServiceRequest(app="ttyd"),
            )

    async def test_start_with_no_wsproxy_addr(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        db_engine: SAEngine,
        scaling_group_fixture: str,
    ) -> None:
        """F-BIZ-5: Scaling group has no wsproxy_addr → ServerError (ServiceUnavailable)."""
        # Ensure wsproxy_addr is NULL on the scaling group
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.update(scaling_groups)
                .where(scaling_groups.c.name == scaling_group_fixture)
                .values(wsproxy_addr=None)
            )

        with pytest.raises(ServerError):
            await admin_registry.session.start_service(
                session_seed.session_name,
                StartServiceRequest(app="ttyd"),
            )

    async def test_start_agent_returns_failed_status(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        db_engine: SAEngine,
        scaling_group_fixture: str,
        agent_registry: AsyncMock,
        appproxy_client_pool: AsyncMock,
    ) -> None:
        """F-BIZ-6: Agent returns status='failed' → ServerError (InternalServerError)."""
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.update(scaling_groups)
                .where(scaling_groups.c.name == scaling_group_fixture)
                .values(wsproxy_addr=_WSPROXY_ADDR)
            )
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.update(kernels)
                .where(kernels.c.id == session_seed.kernel_id)
                .values(
                    service_ports=_SERVICE_PORTS_TTYD,
                    agent_addr="tcp://127.0.0.1:6001",
                    kernel_host="127.0.0.1",
                )
            )

        mock_status = MagicMock()
        mock_status.advertise_address = _WSPROXY_ADDR
        mock_client = AsyncMock()
        mock_client.fetch_status.return_value = mock_status
        appproxy_client_pool.load_client.return_value = mock_client

        agent_registry.increment_session_usage.return_value = None
        agent_registry.start_service.return_value = {
            "status": "failed",
            "error": "service launch failed",
        }

        with pytest.raises(ServerError):
            await admin_registry.session.start_service(
                session_seed.session_name,
                StartServiceRequest(app="ttyd"),
            )


# ---------------------------------------------------------------------------
# Shutdown service endpoint
# ---------------------------------------------------------------------------


class TestSessionShutdownService:
    """Shutdown service endpoint."""

    async def test_shutdown_service_success(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        agent_registry: AsyncMock,
    ) -> None:
        """S-7: Shutdown service 'ttyd' → success, agent_registry.shutdown_service called."""
        agent_registry.shutdown_service.return_value = None

        await admin_registry.session.shutdown_service(
            session_seed.session_name,
            ShutdownServiceRequest(service_name="ttyd"),
        )

        agent_registry.shutdown_service.assert_called_once()

    async def test_shutdown_nonexistent_session(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """F-BIZ-7: Shutdown service on nonexistent session → NotFoundError."""
        with pytest.raises(NotFoundError):
            await admin_registry.session.shutdown_service(
                "nonexistent-session-xyz-99999",
                ShutdownServiceRequest(service_name="ttyd"),
            )
