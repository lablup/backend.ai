from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import AsyncGenerator, AsyncIterator, Mapping
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.auth import PublicKey, SecretKey
from ai.backend.common.config import (
    ModelConfig,
    ModelDefinition,
    ModelHealthCheck,
    ModelServiceConfig,
)
from ai.backend.common.events.event_types.session.broadcast import SchedulingBroadcastEvent
from ai.backend.common.events.types import AbstractEvent
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.common.types import (
    SessionId,
)
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.errors.kernel import SessionNotFound
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.registry import AgentRegistry, _session_terminated_error


class DummyEtcd:
    async def get_prefix(self, key: str) -> Mapping[str, Any]:
        return {}

    async def get(self, key: str) -> Any:
        return None


@pytest.fixture
async def registry_ctx() -> AsyncGenerator[
    tuple[
        AgentRegistry, MagicMock, MagicMock, MagicMock, ManagerConfigProvider, MagicMock, MagicMock
    ],
    None,
]:
    mocked_etcd = DummyEtcd()
    mock_etcd_config_loader = MagicMock()
    mock_etcd_config_loader.update_resource_slots = AsyncMock()
    mock_etcd_config_loader._etcd = mocked_etcd

    mock_loader = MagicMock()
    mock_loader.load = AsyncMock(
        return_value={
            "db": {"name": "test_db", "user": "postgres", "password": "develove"},
            "logging": {},
        }
    )
    mock_config_provider = await ManagerConfigProvider.create(
        loader=mock_loader,
        etcd_watcher=MagicMock(),
        legacy_etcd_config_loader=mock_etcd_config_loader,
    )
    mock_db = MagicMock()
    mock_dbconn = MagicMock()
    mock_dbsess = MagicMock()
    mock_dbconn_ctx = MagicMock()
    mock_dbsess_ctx = MagicMock()
    mock_dbresult = MagicMock()
    mock_dbresult.rowcount = 1
    mock_agent_cache = MagicMock()
    mock_db.connect = MagicMock(return_value=mock_dbconn_ctx)
    mock_db.begin = MagicMock(return_value=mock_dbconn_ctx)
    mock_db.begin_session = MagicMock(return_value=mock_dbsess_ctx)
    mock_dbconn_ctx.__aenter__ = AsyncMock(return_value=mock_dbconn)
    mock_dbconn_ctx.__aexit__ = AsyncMock()
    mock_dbsess_ctx.__aenter__ = AsyncMock(return_value=mock_dbsess)
    mock_dbsess_ctx.__aexit__ = AsyncMock()
    mock_dbconn.execute = AsyncMock(return_value=mock_dbresult)
    mock_dbconn.begin = MagicMock(return_value=mock_dbconn_ctx)
    mock_dbsess.execute = AsyncMock(return_value=mock_dbresult)
    mock_dbsess.begin_session = AsyncMock(return_value=mock_dbsess_ctx)
    mock_valkey_stat_client = MagicMock()
    mock_redis_live = MagicMock()
    mock_redis_live.hset = AsyncMock()
    mock_redis_image = AsyncMock()
    mock_redis_image.close = AsyncMock()
    mock_redis_image.get_all_agents_images = AsyncMock(return_value=[])
    mock_redis_image.get_agent_images = AsyncMock(return_value=[])
    mock_redis_image.add_agent_image = AsyncMock()
    mock_redis_image.remove_agent_image = AsyncMock()
    mock_redis_image.remove_agent = AsyncMock()
    mock_redis_image.clear_all_images = AsyncMock()
    mock_event_dispatcher = MagicMock()
    mock_event_producer = MagicMock()
    mock_event_producer.anycast_event = AsyncMock()
    mock_event_producer.broadcast_event = AsyncMock()
    mock_event_producer.anycast_and_broadcast_event = AsyncMock()

    mock_event_hub = MagicMock()
    mock_event_hub.publish = AsyncMock()
    mock_event_hub.subscribe = AsyncMock()
    mock_event_hub.unsubscribe = AsyncMock()

    hook_plugin_ctx = HookPluginContext(mocked_etcd, {})  # type: ignore
    network_plugin_ctx = NetworkPluginContext(mocked_etcd, {})  # type: ignore

    mock_scheduling_controller = AsyncMock()
    mock_scheduling_controller.enqueue_session = AsyncMock(return_value=SessionId(uuid.uuid4()))
    mock_scheduling_controller.dispatch_session_events = AsyncMock()

    mock_agent_client_pool = MagicMock()

    registry = AgentRegistry(
        config_provider=mock_config_provider,
        db=mock_db,
        agent_cache=mock_agent_cache,
        agent_client_pool=mock_agent_client_pool,
        valkey_stat=mock_valkey_stat_client,
        valkey_live=mock_redis_live,
        valkey_image=mock_redis_image,
        event_producer=mock_event_producer,
        event_hub=mock_event_hub,
        storage_manager=None,  # type: ignore
        hook_plugin_ctx=hook_plugin_ctx,
        network_plugin_ctx=network_plugin_ctx,
        scheduling_controller=mock_scheduling_controller,
        scheduler_repository=MagicMock(),
        ops_provider=MagicMock(),
        manager_public_key=PublicKey(b"GqK]ZYY#h*9jAQbGxSwkeZX3Y*%b+DiY$7ju6sh{"),
        manager_secret_key=SecretKey(b"37KX6]ac^&hcnSaVo=-%eVO9M]ENe8v=BOWF(Sw$"),
    )
    await registry.init()
    try:
        yield (
            registry,
            mock_dbconn,
            mock_dbsess,
            mock_dbresult,
            mock_config_provider,
            mock_event_dispatcher,
            mock_event_producer,
        )
    finally:
        await registry.shutdown()


@dataclass
class MockEndpointData:
    """Minimal stand-in for ``EndpointData`` exposing only ``model_definition``.

    The runtime health-check path reads exactly that field — the persisted
    merged result from the revision — and nothing else.
    """

    model_definition: ModelDefinition | None


class TestResolveHealthCheck:
    """Tests for ``AgentRegistry._resolve_health_check``."""

    def test_returns_stored_health_check(self) -> None:
        endpoint = MockEndpointData(
            model_definition=ModelDefinition(
                models=[
                    ModelConfig(
                        name="m",
                        model_path="/models/m",
                        service=ModelServiceConfig(
                            start_command="run",
                            port=8000,
                            health_check=ModelHealthCheck(
                                enable=True,
                                path="/custom",
                                interval=5.0,
                                max_retries=3,
                                max_wait_time=30.0,
                                expected_status_code=201,
                                initial_delay=120.0,
                            ),
                        ),
                    )
                ]
            )
        )
        result = AgentRegistry._resolve_health_check(endpoint)  # type: ignore[arg-type]
        assert result is not None
        assert result.path == "/custom"
        assert result.interval == 5.0
        assert result.max_retries == 3
        assert result.max_wait_time == 30.0
        assert result.expected_status_code == 201
        assert result.initial_delay == 120.0

    def test_returns_none_when_no_model_definition(self) -> None:
        endpoint = MockEndpointData(model_definition=None)
        assert AgentRegistry._resolve_health_check(endpoint) is None  # type: ignore[arg-type]

    def test_returns_none_when_no_health_check_in_definition(self) -> None:
        endpoint = MockEndpointData(
            model_definition=ModelDefinition(
                models=[
                    ModelConfig(
                        name="m",
                        model_path="/models/m",
                        service=ModelServiceConfig(start_command="run", port=8000),
                    )
                ]
            )
        )
        assert AgentRegistry._resolve_health_check(endpoint) is None  # type: ignore[arg-type]


def _make_scheduling_event(
    session_id: SessionId,
    status: str,
) -> SchedulingBroadcastEvent:
    return SchedulingBroadcastEvent(
        session_id=session_id,
        creation_id="test-creation",
        status_transition=status,
        reason="test",
    )


class TestResourceEntriesFromLegacyDict:
    """Tests for ``AgentRegistry._resource_entries_from_legacy_dict``."""

    def test_drops_zero_quantity_slots(self) -> None:
        entries = AgentRegistry._resource_entries_from_legacy_dict({
            "cpu": 1,
            "mem": "1140850688",
            "cuda.device": 0,
            "cuda.shares": "0",
        })
        assert {str(e.resource_type): e.quantity for e in entries} == {
            "cpu": "1",
            "mem": "1140850688",
        }

    def test_normalizes_binary_size_shortcuts(self) -> None:
        entries = AgentRegistry._resource_entries_from_legacy_dict({
            "mem": "1g",
            "cuda.shares": "0.5",
        })
        assert {str(e.resource_type): e.quantity for e in entries} == {
            "mem": str(1024**3),
            "cuda.shares": "0.5",
        }


class TestWaitForSessionRunning:
    """Tests for _wait_for_session_running() timeout behavior."""

    @pytest.fixture
    def session_id(self) -> SessionId:
        return SessionId(uuid.uuid4())

    @pytest.fixture
    def mock_propagator(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def mock_registry_obj(self) -> MagicMock:
        """Create a minimal mock with db for the registry instance."""
        registry = MagicMock(spec=AgentRegistry)
        registry._wait_for_session_running = AgentRegistry._wait_for_session_running.__get__(
            registry, AgentRegistry
        )
        return registry

    async def test_max_wait_positive_times_out_after_specified_seconds(
        self,
        session_id: SessionId,
        mock_propagator: MagicMock,
        mock_registry_obj: MagicMock,
    ) -> None:
        """max_wait=2 should raise TimeoutError after ~2 seconds, not 60."""

        async def _hang_forever(cache_id: str) -> AsyncIterator[AbstractEvent]:
            await asyncio.Event().wait()  # blocks until cancelled by timeout
            yield  # type: ignore[misc]  # make it an async generator

        mock_propagator.receive = _hang_forever

        start = time.monotonic()
        with pytest.raises(TimeoutError):
            await mock_registry_obj._wait_for_session_running(
                session_id, mock_propagator, max_wait=2
            )
        elapsed = time.monotonic() - start
        assert elapsed < 5, f"Timed out in {elapsed}s, expected ~2s"
        assert elapsed >= 1.5, f"Timed out too fast in {elapsed}s, expected ~2s"

    async def test_max_wait_zero_uses_default_timeout_and_retries(
        self,
        session_id: SessionId,
        mock_propagator: MagicMock,
        mock_registry_obj: MagicMock,
    ) -> None:
        """max_wait=0 should NOT raise TimeoutError; it retries after timeout and checks DB."""
        call_count = 0

        async def _hang_then_stop(cache_id: str) -> AsyncIterator[AbstractEvent]:
            nonlocal call_count
            call_count += 1
            await asyncio.Event().wait()
            yield  # type: ignore[misc]

        mock_propagator.receive = _hang_then_stop

        # Mock DB to return RUNNING status on the fallback check
        mock_db_session = AsyncMock()
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.status = SessionStatus.RUNNING
        mock_result.first.return_value = mock_row
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        mock_db_ctx = MagicMock()
        mock_db_ctx.__aenter__ = AsyncMock(return_value=mock_db_session)
        mock_db_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_registry_obj.db = MagicMock()
        mock_registry_obj.db.begin_readonly_session = MagicMock(return_value=mock_db_ctx)

        # With max_wait=0, the method should catch TimeoutError, check DB, and return
        # We use a short timeout by patching DEFAULT_WAIT_TIMEOUT_SECONDS
        with patch("ai.backend.manager.registry.DEFAULT_WAIT_TIMEOUT_SECONDS", 1):
            await mock_registry_obj._wait_for_session_running(
                session_id, mock_propagator, max_wait=0
            )

        assert call_count >= 1

    async def test_running_event_returns_immediately(
        self,
        session_id: SessionId,
        mock_propagator: MagicMock,
        mock_registry_obj: MagicMock,
    ) -> None:
        """Session becoming RUNNING should cause immediate return."""

        async def _yield_running(cache_id: str) -> AsyncIterator[AbstractEvent]:
            yield _make_scheduling_event(session_id, str(SessionStatus.RUNNING))

        mock_propagator.receive = _yield_running

        start = time.monotonic()
        await mock_registry_obj._wait_for_session_running(session_id, mock_propagator, max_wait=15)
        elapsed = time.monotonic() - start
        assert elapsed < 1, f"Should return immediately, took {elapsed}s"

    async def test_max_wait_zero_db_not_found_raises_session_not_found(
        self,
        session_id: SessionId,
        mock_propagator: MagicMock,
        mock_registry_obj: MagicMock,
    ) -> None:
        """max_wait=0 timeout + session not found in DB should raise SessionNotFound."""

        async def _hang(cache_id: str) -> AsyncIterator[AbstractEvent]:
            await asyncio.Event().wait()
            yield  # type: ignore[misc]

        mock_propagator.receive = _hang

        mock_db_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.first.return_value = None  # session not found in DB
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        mock_db_ctx = MagicMock()
        mock_db_ctx.__aenter__ = AsyncMock(return_value=mock_db_session)
        mock_db_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_registry_obj.db = MagicMock()
        mock_registry_obj.db.begin_readonly_session = MagicMock(return_value=mock_db_ctx)

        with patch("ai.backend.manager.registry.DEFAULT_WAIT_TIMEOUT_SECONDS", 1):
            with pytest.raises(SessionNotFound):
                await mock_registry_obj._wait_for_session_running(
                    session_id, mock_propagator, max_wait=0
                )

    async def test_terminated_event_raises_error_with_stored_reason(
        self,
        session_id: SessionId,
        mock_propagator: MagicMock,
        mock_registry_obj: MagicMock,
    ) -> None:
        """A TERMINATED event should raise SessionNotFound naming the stored error."""

        async def _yield_terminated(cache_id: str) -> AsyncIterator[AbstractEvent]:
            yield _make_scheduling_event(session_id, str(SessionStatus.TERMINATED))

        mock_propagator.receive = _yield_terminated
        mock_db_session = AsyncMock()
        mock_db_session.scalar = AsyncMock(
            return_value={"error": {"error": {"name": "ContainerCreationError", "repr": "boom"}}}
        )
        mock_db_ctx = MagicMock()
        mock_db_ctx.__aenter__ = AsyncMock(return_value=mock_db_session)
        mock_db_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_registry_obj.db = MagicMock()
        mock_registry_obj.db.begin_readonly_session = MagicMock(return_value=mock_db_ctx)

        with pytest.raises(SessionNotFound) as exc_info:
            await mock_registry_obj._wait_for_session_running(
                session_id, mock_propagator, max_wait=15
            )
        assert exc_info.value.extra_msg == (
            "Session terminated during scheduling: ContainerCreationError: boom"
        )

    async def test_max_wait_zero_db_terminated_raises_error_with_stored_reason(
        self,
        session_id: SessionId,
        mock_propagator: MagicMock,
        mock_registry_obj: MagicMock,
    ) -> None:
        """max_wait=0 timeout + TERMINATED in DB should raise SessionNotFound naming the error."""

        async def _hang(cache_id: str) -> AsyncIterator[AbstractEvent]:
            await asyncio.Event().wait()
            yield  # type: ignore[misc]

        mock_propagator.receive = _hang

        mock_db_session = AsyncMock()
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.status = SessionStatus.TERMINATED
        mock_row.status_data = {
            "error": {"error": {"name": "ContainerCreationError", "repr": "boom"}}
        }
        mock_result.first.return_value = mock_row
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_ctx = MagicMock()
        mock_db_ctx.__aenter__ = AsyncMock(return_value=mock_db_session)
        mock_db_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_registry_obj.db = MagicMock()
        mock_registry_obj.db.begin_readonly_session = MagicMock(return_value=mock_db_ctx)

        with patch("ai.backend.manager.registry.DEFAULT_WAIT_TIMEOUT_SECONDS", 1):
            with pytest.raises(SessionNotFound) as exc_info:
                await mock_registry_obj._wait_for_session_running(
                    session_id, mock_propagator, max_wait=0
                )
        assert exc_info.value.extra_msg == (
            "Session terminated during scheduling: ContainerCreationError: boom"
        )


class TestSessionTerminatedError:
    """Tests for the message of the error raised when a session terminates before it runs."""

    @pytest.mark.parametrize(
        ("status_data", "expected"),
        [
            (
                {"error": {"src": "agent", "name": "ContainerCreationError", "repr": "boom"}},
                "Session terminated during scheduling: ContainerCreationError: boom",
            ),
            (
                {"error": {"name": "ImageNotAvailable", "repr": "ImageNotAvailable('x')"}},
                "Session terminated during scheduling: ImageNotAvailable('x')",
            ),
            (
                {"error": {"name": "ContainerCreationError"}},
                "Session terminated during scheduling: ContainerCreationError",
            ),
            (
                {
                    "error": {
                        "error": {"src": "agent", "name": "ContainerCreationError", "repr": "boom"}
                    }
                },
                "Session terminated during scheduling: ContainerCreationError: boom",
            ),
            (
                {
                    "error": {
                        "error": {
                            "name": "MultiAgentError",
                            "repr": "MultiAgentError(2)",
                            "collection": [
                                {"name": "ImageNotAvailable", "repr": "ImageNotAvailable('x')"},
                                {"name": "ResourceError", "repr": "ResourceError()"},
                            ],
                        }
                    }
                },
                "Session terminated during scheduling: ImageNotAvailable('x') (+1 more)",
            ),
            (
                {"error": {"name": "ContainerCreationError", "repr": "line1\nline2\n  line3"}},
                "Session terminated during scheduling: ContainerCreationError: line1 line2 line3",
            ),
            ({}, "Session terminated during scheduling"),
            (None, "Session terminated during scheduling"),
        ],
        ids=[
            "name-and-repr",
            "repr-starts-with-name",
            "name-only",
            "nested",
            "multi-agent",
            "newlines-collapsed",
            "no-error",
            "no-status-data",
        ],
    )
    def test_message_names_stored_error(
        self, status_data: dict[str, Any] | None, expected: str
    ) -> None:
        err = _session_terminated_error(status_data)
        assert isinstance(err, SessionNotFound)
        assert err.extra_msg == expected

    def test_long_reason_is_truncated(self) -> None:
        err = _session_terminated_error({"error": {"name": "E", "repr": "x" * 2000}})
        assert err.extra_msg is not None
        reason = err.extra_msg.removeprefix("Session terminated during scheduling: ")
        assert len(reason) == 512
        assert reason.endswith("\u2026")

    def test_traceback_is_never_included(self) -> None:
        err = _session_terminated_error({
            "error": {"name": "E", "repr": "boom", "traceback": "secret-tb", "agent_id": "i-a"}
        })
        assert err.extra_msg is not None
        assert "secret-tb" not in err.extra_msg
        assert "i-a" not in err.extra_msg
