from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import AsyncGenerator, AsyncIterator, Mapping
from dataclasses import dataclass
from decimal import Decimal
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
    BinarySize,
    DeviceId,
    SessionId,
    SlotName,
)
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.errors.kernel import SessionNotFound
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.registry import AgentRegistry


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


async def test_convert_resource_spec_to_resource_slot(
    registry_ctx: tuple[
        AgentRegistry, MagicMock, MagicMock, MagicMock, ManagerConfigProvider, MagicMock, MagicMock
    ],
) -> None:
    registry, _, _, _, _, _, _ = registry_ctx
    allocations = {
        "cuda": {
            SlotName("cuda.shares"): {
                DeviceId("a0"): "2.5",
                DeviceId("a1"): "2.0",
            },
        },
    }
    converted_allocations = registry.convert_resource_spec_to_resource_slot(allocations)
    assert converted_allocations["cuda.shares"] == Decimal("4.5")
    allocations = {
        "cpu": {
            SlotName("cpu"): {
                DeviceId("a0"): "3",
                DeviceId("a1"): "1",
            },
        },
        "ram": {
            SlotName("ram"): {
                DeviceId("b0"): "2.5g",
                DeviceId("b1"): "512m",
            },
        },
    }
    converted_allocations = registry.convert_resource_spec_to_resource_slot(allocations)
    assert converted_allocations["cpu"] == Decimal("4")
    assert converted_allocations["ram"] == Decimal(BinarySize.from_str("1g")) * 3


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
                            start_command=["run"],
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
                        service=ModelServiceConfig(start_command=["run"], port=8000),
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


class TestMountEntriesFromCreationConfig:
    """Session creation honors ``mount_destination`` from both ``mount_id_map``
    (preferred) and ``mount_options[uuid].mount_destination`` (fallback), so the
    same ``MountOption`` shape that inference service creation accepts also
    works for sessions.
    """

    def test_mount_id_map_supplies_destination(self) -> None:
        vfid = uuid.uuid4()
        creation_config = {
            "mount_ids": [vfid],
            "mount_id_map": {vfid: "/data/dst"},
            "mount_options": {vfid: {"permission": "ro"}},
        }

        entries = AgentRegistry._mount_entries_from_creation_config(creation_config)

        assert len(entries) == 1
        assert entries[0].mount_destination == "/data/dst"

    def test_mount_options_mount_destination_fallback(self) -> None:
        vfid = uuid.uuid4()
        creation_config = {
            "mount_ids": [vfid],
            "mount_id_map": {},
            "mount_options": {
                vfid: {"mount_destination": "/data/from-options", "permission": "ro"},
            },
        }

        entries = AgentRegistry._mount_entries_from_creation_config(creation_config)

        assert len(entries) == 1
        assert entries[0].mount_destination == "/data/from-options"

    def test_mount_id_map_takes_precedence_over_mount_options(self) -> None:
        vfid = uuid.uuid4()
        creation_config = {
            "mount_ids": [vfid],
            "mount_id_map": {vfid: "/data/winner"},
            "mount_options": {vfid: {"mount_destination": "/data/loser"}},
        }

        entries = AgentRegistry._mount_entries_from_creation_config(creation_config)

        assert len(entries) == 1
        assert entries[0].mount_destination == "/data/winner"
