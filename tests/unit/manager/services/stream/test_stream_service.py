from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.types import AccessKey, KernelId, SessionId
from ai.backend.manager.errors.kernel import SessionNotFound
from ai.backend.manager.idle import AppStreamingStatus, IdleCheckerHost
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.stream.repository import StreamRepository
from ai.backend.manager.services.stream.actions.execute_in_stream import (
    ExecuteInStreamAction,
    ExecuteInStreamActionResult,
)
from ai.backend.manager.services.stream.actions.gc_stale_connections import (
    GCStaleConnectionsAction,
    GCStaleConnectionsActionResult,
)
from ai.backend.manager.services.stream.actions.get_streaming_session import (
    GetStreamingSessionAction,
    GetStreamingSessionActionResult,
)
from ai.backend.manager.services.stream.actions.interrupt_in_stream import (
    InterruptInStreamAction,
    InterruptInStreamActionResult,
)
from ai.backend.manager.services.stream.actions.restart_in_stream import (
    RestartInStreamAction,
    RestartInStreamActionResult,
)
from ai.backend.manager.services.stream.actions.start_service_in_stream import (
    StartServiceInStreamAction,
    StartServiceInStreamActionResult,
)
from ai.backend.manager.services.stream.actions.track_connection import (
    TrackConnectionAction,
    TrackConnectionActionResult,
)
from ai.backend.manager.services.stream.actions.untrack_connection import (
    UntrackConnectionAction,
    UntrackConnectionActionResult,
)
from ai.backend.manager.services.stream.service import StreamService

FAKE_SESSION_ID = SessionId(uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"))
FAKE_KERNEL_ID = KernelId(uuid.UUID("11111111-2222-3333-4444-555555555555"))
FAKE_ACCESS_KEY = AccessKey("AKIAIOSFODNN7EXAMPLE")


class TestStreamService:
    @pytest.fixture
    def mock_repository(self) -> AsyncMock:
        return AsyncMock(spec=StreamRepository)

    @pytest.fixture
    def mock_registry(self) -> AsyncMock:
        return AsyncMock(spec=AgentRegistry)

    @pytest.fixture
    def mock_valkey_live(self) -> AsyncMock:
        return AsyncMock(spec=ValkeyLiveClient)

    @pytest.fixture
    def mock_idle_checker_host(self) -> AsyncMock:
        return AsyncMock(spec=IdleCheckerHost)

    @pytest.fixture
    def mock_etcd(self) -> AsyncMock:
        return AsyncMock(spec=AsyncEtcd)

    @pytest.fixture
    def stream_service(
        self,
        mock_repository: AsyncMock,
        mock_registry: AsyncMock,
        mock_valkey_live: AsyncMock,
        mock_idle_checker_host: AsyncMock,
        mock_etcd: AsyncMock,
    ) -> StreamService:
        return StreamService(
            repository=mock_repository,
            registry=mock_registry,
            valkey_live=mock_valkey_live,
            idle_checker_host=mock_idle_checker_host,
            etcd=mock_etcd,
        )

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        session = MagicMock(spec=SessionRow)
        session.id = FAKE_SESSION_ID
        kernel = MagicMock()
        kernel.id = FAKE_KERNEL_ID
        kernel.kernel_host = "10.0.0.1"
        kernel.agent_addr = "agent1:6001"
        kernel.repl_in_port = 2000
        kernel.repl_out_port = 2001
        kernel.service_ports = [{"name": "jupyter", "protocol": "http", "container_ports": [8080]}]
        session.main_kernel = kernel
        return session


class TestGetStreamingSession(TestStreamService):
    async def test_valid_session_returns_full_info(
        self,
        stream_service: StreamService,
        mock_repository: AsyncMock,
        mock_session: MagicMock,
    ) -> None:
        mock_repository.get_streaming_session.return_value = mock_session
        action = GetStreamingSessionAction(
            session_name="my-session",
            access_key=FAKE_ACCESS_KEY,
        )

        result = await stream_service.get_streaming_session(action)

        assert isinstance(result, GetStreamingSessionActionResult)
        assert result.session_id == str(FAKE_SESSION_ID)
        assert result.kernel_id == str(FAKE_KERNEL_ID)
        assert result.kernel_host == "10.0.0.1"
        assert result.agent_addr == "agent1:6001"
        assert result.repl_in_port == 2000
        assert result.repl_out_port == 2001
        assert result.service_ports == [
            {"name": "jupyter", "protocol": "http", "container_ports": [8080]}
        ]
        mock_repository.get_streaming_session.assert_awaited_once_with(
            "my-session", FAKE_ACCESS_KEY
        )

    async def test_no_service_ports_returns_empty_list(
        self,
        stream_service: StreamService,
        mock_repository: AsyncMock,
        mock_session: MagicMock,
    ) -> None:
        mock_session.main_kernel.service_ports = None
        mock_repository.get_streaming_session.return_value = mock_session
        action = GetStreamingSessionAction(
            session_name="my-session",
            access_key=FAKE_ACCESS_KEY,
        )

        result = await stream_service.get_streaming_session(action)

        assert result.service_ports == []

    async def test_non_existent_session_raises(
        self,
        stream_service: StreamService,
        mock_repository: AsyncMock,
    ) -> None:
        mock_repository.get_streaming_session.side_effect = SessionNotFound()
        action = GetStreamingSessionAction(
            session_name="nonexistent",
            access_key=FAKE_ACCESS_KEY,
        )

        with pytest.raises(SessionNotFound):
            await stream_service.get_streaming_session(action)


class TestExecuteInStream(TestStreamService):
    async def test_valid_params_return_agent_result(
        self,
        stream_service: StreamService,
        mock_repository: AsyncMock,
        mock_registry: AsyncMock,
        mock_session: MagicMock,
    ) -> None:
        mock_repository.get_streaming_session.return_value = mock_session
        mock_registry.execute.return_value = {"status": "finished", "exitCode": 0}
        action = ExecuteInStreamAction(
            session_name="my-session",
            access_key=FAKE_ACCESS_KEY,
            api_version=(4, "websocket"),
            run_id="run-001",
            mode="query",
            code="print('hello')",
            opts={},
            flush_timeout=2.0,
        )

        result = await stream_service.execute_in_stream(action)

        assert isinstance(result, ExecuteInStreamActionResult)
        assert result.result == {"status": "finished", "exitCode": 0}
        mock_registry.execute.assert_awaited_once_with(
            mock_session,
            (4, "websocket"),
            "run-001",
            "query",
            "print('hello')",
            {},
            flush_timeout=2.0,
        )

    async def test_flush_timeout_passed_to_agent(
        self,
        stream_service: StreamService,
        mock_repository: AsyncMock,
        mock_registry: AsyncMock,
        mock_session: MagicMock,
    ) -> None:
        mock_repository.get_streaming_session.return_value = mock_session
        mock_registry.execute.return_value = {"status": "finished"}
        action = ExecuteInStreamAction(
            session_name="my-session",
            access_key=FAKE_ACCESS_KEY,
            api_version=(3, "batch"),
            run_id="run-002",
            mode="batch",
            code="x = 1",
            flush_timeout=10.5,
        )

        await stream_service.execute_in_stream(action)

        _, kwargs = mock_registry.execute.call_args
        assert kwargs["flush_timeout"] == 10.5


class TestInterruptInStream(TestStreamService):
    async def test_returns_agent_interrupt_result(
        self,
        stream_service: StreamService,
        mock_repository: AsyncMock,
        mock_registry: AsyncMock,
        mock_session: MagicMock,
    ) -> None:
        mock_repository.get_streaming_session.return_value = mock_session
        mock_registry.interrupt_session.return_value = {"status": "interrupted"}
        action = InterruptInStreamAction(
            session_name="my-session",
            access_key=FAKE_ACCESS_KEY,
        )

        result = await stream_service.interrupt_in_stream(action)

        assert isinstance(result, InterruptInStreamActionResult)
        assert result.result == {"status": "interrupted"}
        mock_registry.interrupt_session.assert_awaited_once_with(mock_session)


class TestRestartInStream(TestStreamService):
    async def test_restart_calls_registry(
        self,
        stream_service: StreamService,
        mock_repository: AsyncMock,
        mock_registry: AsyncMock,
        mock_session: MagicMock,
    ) -> None:
        mock_repository.get_streaming_session.return_value = mock_session
        mock_registry.restart_session.return_value = None
        action = RestartInStreamAction(
            session_name="my-session",
            access_key=FAKE_ACCESS_KEY,
        )

        result = await stream_service.restart_in_stream(action)

        assert isinstance(result, RestartInStreamActionResult)
        mock_registry.restart_session.assert_awaited_once_with(mock_session)


class TestStartServiceInStream(TestStreamService):
    async def test_valid_service_returns_result(
        self,
        stream_service: StreamService,
        mock_repository: AsyncMock,
        mock_registry: AsyncMock,
        mock_session: MagicMock,
    ) -> None:
        mock_repository.get_streaming_session.return_value = mock_session
        mock_registry.start_service.return_value = {"status": "started"}
        action = StartServiceInStreamAction(
            session_name="my-session",
            access_key=FAKE_ACCESS_KEY,
            service="jupyter",
            opts={"port": 8888},
        )

        result = await stream_service.start_service_in_stream(action)

        assert isinstance(result, StartServiceInStreamActionResult)
        assert result.result == {"status": "started"}
        mock_registry.start_service.assert_awaited_once_with(
            mock_session, "jupyter", {"port": 8888}
        )


class TestTrackConnection(TestStreamService):
    async def test_track_updates_valkey_and_idle_checker(
        self,
        stream_service: StreamService,
        mock_valkey_live: AsyncMock,
        mock_idle_checker_host: AsyncMock,
    ) -> None:
        action = TrackConnectionAction(
            kernel_id=FAKE_KERNEL_ID,
            session_id=FAKE_SESSION_ID,
            service="jupyter",
            stream_id="stream-001",
        )

        result = await stream_service.track_connection(action)

        assert isinstance(result, TrackConnectionActionResult)
        assert result.kernel_id == str(FAKE_KERNEL_ID)
        mock_valkey_live.update_connection_tracker.assert_awaited_once_with(
            str(FAKE_KERNEL_ID), "jupyter", "stream-001"
        )
        mock_idle_checker_host.update_app_streaming_status.assert_awaited_once_with(
            FAKE_SESSION_ID,
            AppStreamingStatus.HAS_ACTIVE_CONNECTIONS,
        )

    async def test_re_registration_calls_same_methods(
        self,
        stream_service: StreamService,
        mock_valkey_live: AsyncMock,
        mock_idle_checker_host: AsyncMock,
    ) -> None:
        action = TrackConnectionAction(
            kernel_id=FAKE_KERNEL_ID,
            session_id=FAKE_SESSION_ID,
            service="jupyter",
            stream_id="stream-001",
        )

        await stream_service.track_connection(action)
        await stream_service.track_connection(action)

        assert mock_valkey_live.update_connection_tracker.await_count == 2
        assert mock_idle_checker_host.update_app_streaming_status.await_count == 2


class TestUntrackConnection(TestStreamService):
    async def test_last_connection_triggers_no_active(
        self,
        stream_service: StreamService,
        mock_valkey_live: AsyncMock,
        mock_idle_checker_host: AsyncMock,
    ) -> None:
        mock_valkey_live.count_active_connections.return_value = 0
        action = UntrackConnectionAction(
            kernel_id=FAKE_KERNEL_ID,
            session_id=FAKE_SESSION_ID,
            service="jupyter",
            stream_id="stream-001",
        )

        result = await stream_service.untrack_connection(action)

        assert isinstance(result, UntrackConnectionActionResult)
        assert result.remaining_count == 0
        mock_valkey_live.remove_connection_tracker.assert_awaited_once_with(
            str(FAKE_KERNEL_ID), "jupyter", "stream-001"
        )
        mock_idle_checker_host.update_app_streaming_status.assert_awaited_once_with(
            FAKE_SESSION_ID,
            AppStreamingStatus.NO_ACTIVE_CONNECTIONS,
        )

    async def test_remaining_connections_does_not_trigger_no_active(
        self,
        stream_service: StreamService,
        mock_valkey_live: AsyncMock,
        mock_idle_checker_host: AsyncMock,
    ) -> None:
        mock_valkey_live.count_active_connections.return_value = 3
        action = UntrackConnectionAction(
            kernel_id=FAKE_KERNEL_ID,
            session_id=FAKE_SESSION_ID,
            service="jupyter",
            stream_id="stream-002",
        )

        result = await stream_service.untrack_connection(action)

        assert result.remaining_count == 3
        mock_idle_checker_host.update_app_streaming_status.assert_not_awaited()


class TestGCStaleConnections(TestStreamService):
    async def test_removes_stale_and_reports_sessions(
        self,
        stream_service: StreamService,
        mock_valkey_live: AsyncMock,
        mock_idle_checker_host: AsyncMock,
        mock_etcd: AsyncMock,
    ) -> None:
        mock_etcd.get.return_value = "10m"
        mock_valkey_live.get_server_time.return_value = 1000.0
        sid = str(FAKE_SESSION_ID)

        # prev_remaining=2, removed_count=2, remaining=0 → session goes idle
        mock_valkey_live.count_active_connections.side_effect = [2, 0]
        mock_valkey_live.remove_stale_connections.return_value = 2

        action = GCStaleConnectionsAction(active_session_ids=[KernelId(FAKE_SESSION_ID)])

        result = await stream_service.gc_stale_connections(action)

        assert isinstance(result, GCStaleConnectionsActionResult)
        assert sid in result.removed_sessions
        mock_idle_checker_host.update_app_streaming_status.assert_awaited_once_with(
            SessionId(uuid.UUID(sid)),
            AppStreamingStatus.NO_ACTIVE_CONNECTIONS,
        )

    async def test_empty_session_ids_returns_empty(
        self,
        stream_service: StreamService,
        mock_valkey_live: AsyncMock,
        mock_etcd: AsyncMock,
    ) -> None:
        mock_etcd.get.return_value = "5m"
        mock_valkey_live.get_server_time.return_value = 1000.0

        action = GCStaleConnectionsAction(active_session_ids=[])

        result = await stream_service.gc_stale_connections(action)

        assert result.removed_sessions == []

    async def test_etcd_none_uses_default_timeout(
        self,
        stream_service: StreamService,
        mock_valkey_live: AsyncMock,
        mock_etcd: AsyncMock,
    ) -> None:
        mock_etcd.get.return_value = None
        mock_valkey_live.get_server_time.return_value = 1000.0

        action = GCStaleConnectionsAction(active_session_ids=[])

        result = await stream_service.gc_stale_connections(action)

        assert result.removed_sessions == []
        mock_etcd.get.assert_awaited_once_with("config/idle/app-streaming-packet-timeout")

    async def test_active_to_idle_included_in_removed(
        self,
        stream_service: StreamService,
        mock_valkey_live: AsyncMock,
        mock_idle_checker_host: AsyncMock,
        mock_etcd: AsyncMock,
    ) -> None:
        mock_etcd.get.return_value = "5m"
        mock_valkey_live.get_server_time.return_value = 2000.0

        sid1 = KernelId(uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001"))
        sid2 = KernelId(uuid.UUID("aaaaaaaa-0000-0000-0000-000000000002"))

        # sid1: prev=3, remaining=0 → goes idle
        # sid2: prev=5, remaining=2 → stays active
        mock_valkey_live.count_active_connections.side_effect = [3, 0, 5, 2]
        mock_valkey_live.remove_stale_connections.side_effect = [3, 3]

        action = GCStaleConnectionsAction(active_session_ids=[sid1, sid2])

        result = await stream_service.gc_stale_connections(action)

        assert str(sid1) in result.removed_sessions
        assert str(sid2) not in result.removed_sessions
