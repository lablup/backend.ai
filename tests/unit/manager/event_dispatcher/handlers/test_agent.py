from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from ai.backend.common.auth import PublicKey
from ai.backend.common.data.agent.types import AgentInfo
from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.data.entity.resource_slot import ResourceSlotName
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.agent.anycast import (
    AgentHeartbeatEvent,
    AgentStartedEvent,
    AgentTerminatedEvent,
)
from ai.backend.common.plugin.event import EventDispatcherPluginContext
from ai.backend.common.types import (
    AgentId,
    DeviceName,
    ResourceSlotEntry,
    SlotName,
    SlotTypes,
)
from ai.backend.manager.data.agent.types import AgentHeartbeatUpsert, AgentStatus, UpsertResult
from ai.backend.manager.event_dispatcher.handlers.agent import AgentEventHandler
from ai.backend.manager.models.agent.updaters import AgentExitStatusUpdater, AgentStatusUpdater
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.agent.repository import AgentRepository


@pytest.fixture
def agent_uuid() -> AgentUUID:
    return AgentUUID(UUID("00000000-0000-0000-0000-0000000000a1"))


@pytest.fixture
def mock_agent_repository(agent_uuid: AgentUUID) -> AsyncMock:
    mock = AsyncMock(spec=AgentRepository)
    mock.lookup_uuid.return_value = agent_uuid
    return mock


@pytest.fixture
def mock_event_producer() -> AsyncMock:
    return AsyncMock(spec=EventProducer)


@pytest.fixture
def mock_agent_cache() -> MagicMock:
    mock = MagicMock()
    mock.update = MagicMock()
    mock.discard = MagicMock()
    return mock


@pytest.fixture
def mock_hook_plugin_ctx() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_registry(mock_agent_cache: MagicMock, mock_hook_plugin_ctx: AsyncMock) -> MagicMock:
    mock = MagicMock(spec=AgentRegistry)
    mock.agent_cache = mock_agent_cache
    mock.hook_plugin_ctx = mock_hook_plugin_ctx
    return mock


@pytest.fixture
def handler(
    mock_registry: MagicMock,
    mock_agent_repository: AsyncMock,
    mock_event_producer: AsyncMock,
) -> AgentEventHandler:
    return AgentEventHandler(
        mock_registry,
        MagicMock(spec=ExtendedAsyncSAEngine),
        MagicMock(spec=EventDispatcherPluginContext),
        mock_agent_repository,
        mock_event_producer,
    )


@pytest.fixture
def sample_agent_info() -> AgentInfo:
    return AgentInfo(
        ip="192.168.1.100",
        version="24.12.0",
        scaling_group="default",
        available_resource_slots=[
            ResourceSlotEntry(resource_type=ResourceSlotName("cpu"), quantity="8"),
            ResourceSlotEntry(resource_type=ResourceSlotName("mem"), quantity="32768"),
        ],
        slot_key_and_units={
            ResourceSlotName("cpu"): SlotTypes.COUNT,
            ResourceSlotName("mem"): SlotTypes.BYTES,
        },
        addr="tcp://192.168.1.100:6001",
        public_key=PublicKey(b"test-public-key"),
        public_host="192.168.1.100",
        region="us-west-1",
        architecture="x86_64",
        compute_plugins={DeviceName("cpu"): {}},
        auto_terminate_abusing_kernel=False,
    )


class TestHeartbeat:
    async def test_normal_update(
        self,
        handler: AgentEventHandler,
        mock_agent_repository: AsyncMock,
        mock_agent_cache: MagicMock,
        mock_event_producer: AsyncMock,
        mock_hook_plugin_ctx: AsyncMock,
        sample_agent_info: AgentInfo,
    ) -> None:
        agent_id = AgentId("agent-001")
        mock_agent_repository.sync_agent_heartbeat.return_value = UpsertResult(
            was_revived=False,
            need_resource_slot_update=False,
        )
        mock_agent_repository.sync_installed_images.return_value = None

        await handler.handle_agent_heartbeat(
            None, agent_id, AgentHeartbeatEvent(agent_info=sample_agent_info)
        )

        mock_agent_repository.sync_agent_heartbeat.assert_called_once()
        call_args = mock_agent_repository.sync_agent_heartbeat.call_args[0]
        assert call_args[0] == agent_id
        assert isinstance(call_args[1], AgentHeartbeatUpsert)

        mock_agent_cache.update.assert_called_once_with(
            agent_id,
            sample_agent_info.addr,
            sample_agent_info.public_key,
        )
        mock_event_producer.anycast_event.assert_not_called()
        mock_agent_repository.sync_installed_images.assert_called_once_with(agent_id=agent_id)
        mock_hook_plugin_ctx.notify.assert_called_once_with(
            "POST_AGENT_HEARTBEAT",
            (
                agent_id,
                sample_agent_info.scaling_group,
                sample_agent_info.available_resource_slots,
            ),
        )

    async def test_agent_revival_emits_started_event(
        self,
        handler: AgentEventHandler,
        mock_agent_repository: AsyncMock,
        mock_event_producer: AsyncMock,
        sample_agent_info: AgentInfo,
    ) -> None:
        agent_id = AgentId("agent-revival")
        mock_agent_repository.sync_agent_heartbeat.return_value = UpsertResult(
            was_revived=True,
            need_resource_slot_update=False,
        )
        mock_agent_repository.sync_installed_images.return_value = None

        await handler.handle_agent_heartbeat(
            None, agent_id, AgentHeartbeatEvent(agent_info=sample_agent_info)
        )

        mock_event_producer.anycast_event.assert_called_once()
        call_args = mock_event_producer.anycast_event.call_args
        assert isinstance(call_args[0][0], AgentStartedEvent)
        assert call_args[0][0].reason == "revived"
        assert call_args[1]["source_override"] == agent_id

    async def test_new_resource_slots_reach_repository_and_hook(
        self,
        handler: AgentEventHandler,
        mock_agent_repository: AsyncMock,
        mock_hook_plugin_ctx: AsyncMock,
    ) -> None:
        agent_id = AgentId("agent-resource-update")
        agent_info = AgentInfo(
            ip="192.168.1.100",
            version="24.12.0",
            scaling_group="gpu-cluster",
            available_resource_slots=[
                ResourceSlotEntry(resource_type=ResourceSlotName("cpu"), quantity="16"),
                ResourceSlotEntry(resource_type=ResourceSlotName("mem"), quantity="65536"),
                ResourceSlotEntry(resource_type=ResourceSlotName("cuda.shares"), quantity="8"),
            ],
            slot_key_and_units={
                ResourceSlotName("cpu"): SlotTypes.COUNT,
                ResourceSlotName("mem"): SlotTypes.BYTES,
                ResourceSlotName("cuda.shares"): SlotTypes.COUNT,
            },
            addr="tcp://192.168.1.200:6001",
            public_key=PublicKey(b"gpu-node-key"),
            public_host="192.168.1.200",
            region="us-west-2",
            architecture="x86_64",
            compute_plugins={DeviceName("cpu"): {}},
            auto_terminate_abusing_kernel=False,
        )
        mock_agent_repository.sync_agent_heartbeat.return_value = UpsertResult(
            was_revived=False,
            need_resource_slot_update=True,
        )
        mock_agent_repository.sync_installed_images.return_value = None

        await handler.handle_agent_heartbeat(
            None, agent_id, AgentHeartbeatEvent(agent_info=agent_info)
        )

        upsert_data = mock_agent_repository.sync_agent_heartbeat.call_args[0][1]
        assert SlotName("cuda.shares") in upsert_data.resource_info.slot_key_and_units
        hook_args = mock_hook_plugin_ctx.notify.call_args[0]
        assert hook_args[0] == "POST_AGENT_HEARTBEAT"
        assert hook_args[1][2] == agent_info.available_resource_slots

    async def test_concurrent_heartbeats(
        self,
        handler: AgentEventHandler,
        mock_agent_repository: AsyncMock,
        mock_agent_cache: MagicMock,
        mock_hook_plugin_ctx: AsyncMock,
        sample_agent_info: AgentInfo,
    ) -> None:
        agents = [AgentId(f"agent-{i:03d}") for i in range(5)]
        mock_agent_repository.sync_agent_heartbeat.return_value = UpsertResult(
            was_revived=False,
            need_resource_slot_update=False,
        )
        mock_agent_repository.sync_installed_images.return_value = None

        await asyncio.gather(*[
            handler.handle_agent_heartbeat(
                None, agent_id, AgentHeartbeatEvent(agent_info=sample_agent_info)
            )
            for agent_id in agents
        ])

        assert mock_agent_repository.sync_agent_heartbeat.call_count == 5
        assert mock_agent_cache.update.call_count == 5
        assert mock_agent_repository.sync_installed_images.call_count == 5
        assert mock_hook_plugin_ctx.notify.call_count == 5


class TestLifecycle:
    async def test_started_marks_alive(
        self,
        handler: AgentEventHandler,
        mock_agent_repository: AsyncMock,
        agent_uuid: AgentUUID,
    ) -> None:
        agent_id = AgentId("agent-001")

        await handler.handle_agent_started(None, agent_id, AgentStartedEvent(reason="revived"))

        updater = mock_agent_repository.update_agent_status.call_args[0][0]
        assert isinstance(updater, AgentStatusUpdater)
        assert updater.target_id_value() == agent_uuid
        assert updater.status == AgentStatus.ALIVE

    @pytest.mark.parametrize(
        ("reason", "expected_status"),
        [
            ("agent-lost", AgentStatus.LOST),
            ("agent-terminated", AgentStatus.TERMINATED),
        ],
    )
    async def test_terminated_marks_exit(
        self,
        handler: AgentEventHandler,
        mock_agent_repository: AsyncMock,
        mock_agent_cache: MagicMock,
        reason: str,
        expected_status: AgentStatus,
    ) -> None:
        agent_id = AgentId("agent-001")

        await handler.handle_agent_terminated(None, agent_id, AgentTerminatedEvent(reason=reason))

        updater = mock_agent_repository.mark_agent_exit.call_args[0][0]
        assert isinstance(updater, AgentExitStatusUpdater)
        assert updater.status == expected_status
        assert updater.lost_at.optional_value() is not None
        mock_agent_repository.cleanup_agent_caches.assert_called_once_with(agent_id)
        mock_agent_cache.discard.assert_called_once_with(agent_id)

    async def test_restart_keeps_the_agent_and_marks_restarting(
        self,
        handler: AgentEventHandler,
        mock_agent_repository: AsyncMock,
    ) -> None:
        agent_id = AgentId("agent-001")

        await handler.handle_agent_terminated(
            None, agent_id, AgentTerminatedEvent(reason="agent-restart")
        )

        mock_agent_repository.mark_agent_exit.assert_not_called()
        updater = mock_agent_repository.update_agent_status.call_args[0][0]
        assert updater.status == AgentStatus.RESTARTING
