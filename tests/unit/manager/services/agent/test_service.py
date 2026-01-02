import asyncio
from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.auth import PublicKey
from ai.backend.common.data.agent.types import AgentInfo
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.agent.anycast import AgentStartedEvent
from ai.backend.common.exception import AgentWatcherResponseError
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.common.types import AgentId, DeviceName, ResourceSlot, SlotName, SlotTypes
from ai.backend.manager.agent_cache import AgentRPCCache
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.agent.types import AgentHeartbeatUpsert, UpsertResult
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.agent.repository import AgentRepository
from ai.backend.manager.services.agent.actions.get_watcher_status import (
    GetWatcherStatusAction,
)
from ai.backend.manager.services.agent.actions.handle_heartbeat import (
    HandleHeartbeatAction,
    HandleHeartbeatActionResult,
)
from ai.backend.manager.services.agent.actions.watcher_agent_restart import (
    WatcherAgentRestartAction,
)
from ai.backend.manager.services.agent.actions.watcher_agent_start import (
    WatcherAgentStartAction,
)
from ai.backend.manager.services.agent.actions.watcher_agent_stop import (
    WatcherAgentStopAction,
)
from ai.backend.manager.services.agent.service import AgentService


@pytest.fixture
def mock_etcd() -> AsyncMock:
    return AsyncMock(spec=AsyncEtcd)


@pytest.fixture
def mock_agent_registry() -> AsyncMock:
    return AsyncMock(spec=AgentRegistry)


@pytest.fixture
def mock_config_provider() -> MagicMock:
    mock = MagicMock(spec=ManagerConfigProvider)
    mock.config.watcher.token = "test-token"
    return mock


@pytest.fixture
def mock_agent_repository() -> AsyncMock:
    return AsyncMock(spec=AgentRepository)


@pytest.fixture
def mock_hook_plugin_ctx() -> AsyncMock:
    return AsyncMock(spec=HookPluginContext)


@pytest.fixture
def mock_event_producer() -> AsyncMock:
    return AsyncMock(spec=EventProducer)


@pytest.fixture
def mock_agent_cache() -> MagicMock:
    mock = MagicMock(spec=AgentRPCCache)
    mock.update = MagicMock()
    return mock


@pytest.fixture
def agent_service(
    mock_etcd: AsyncMock,
    mock_agent_registry: AsyncMock,
    mock_config_provider: MagicMock,
    mock_agent_repository: AsyncMock,
    mock_hook_plugin_ctx: AsyncMock,
    mock_event_producer: AsyncMock,
    mock_agent_cache: MagicMock,
) -> AgentService:
    return AgentService(
        etcd=mock_etcd,
        agent_registry=mock_agent_registry,
        config_provider=mock_config_provider,
        agent_repository=mock_agent_repository,
        hook_plugin_ctx=mock_hook_plugin_ctx,
        event_producer=mock_event_producer,
        agent_cache=mock_agent_cache,
        scheduler_repository=AsyncMock(),  # Not used in these tests
    )


@pytest.fixture
def sample_agent_info() -> AgentInfo:
    return AgentInfo(
        ip="192.168.1.100",
        version="24.12.0",
        scaling_group="default",
        available_resource_slots=ResourceSlot({
            SlotName("cpu"): "8",
            SlotName("mem"): "32768",
        }),
        slot_key_and_units={
            SlotName("cpu"): SlotTypes.COUNT,
            SlotName("mem"): SlotTypes.BYTES,
        },
        addr="tcp://192.168.1.100:6001",
        public_key=PublicKey(b"test-public-key"),
        public_host="192.168.1.100",
        images=b"\x82\xc4\x00\x00",  # msgpack compressed data
        region="us-west-1",
        architecture="x86_64",
        compute_plugins={DeviceName("cpu"): {}},
        auto_terminate_abusing_kernel=False,
    )


class TestAgentService:
    @pytest.mark.asyncio
    async def test_handle_heartbeat_normal_update(
        self,
        agent_service: AgentService,
        mock_agent_repository: AsyncMock,
        mock_agent_cache: MagicMock,
        mock_event_producer: AsyncMock,
        mock_hook_plugin_ctx: AsyncMock,
        sample_agent_info: AgentInfo,
    ) -> None:
        # Given
        agent_id = AgentId("agent-001")
        action = HandleHeartbeatAction(
            agent_id=agent_id,
            agent_info=sample_agent_info,
        )

        upsert_result = UpsertResult(
            was_revived=False,
            need_resource_slot_update=False,
        )
        mock_agent_repository.sync_agent_heartbeat.return_value = upsert_result
        mock_agent_repository.sync_installed_images.return_value = None

        # When
        result = await agent_service.handle_heartbeat(action)

        # Then
        assert isinstance(result, HandleHeartbeatActionResult)
        assert result.agent_id == agent_id

        # Verify repository calls
        mock_agent_repository.sync_agent_heartbeat.assert_called_once()
        call_args = mock_agent_repository.sync_agent_heartbeat.call_args[0]
        assert call_args[0] == agent_id
        assert isinstance(call_args[1], AgentHeartbeatUpsert)

        # Verify cache update
        mock_agent_cache.update.assert_called_once_with(
            agent_id,
            sample_agent_info.addr,
            sample_agent_info.public_key,
        )

        # Verify no revival event was sent
        mock_event_producer.anycast_event.assert_not_called()

        # Verify image registration
        mock_agent_repository.sync_installed_images.assert_called_once_with(
            agent_id=agent_id,
        )

        # Verify hook notification
        mock_hook_plugin_ctx.notify.assert_called_once_with(
            "POST_AGENT_HEARTBEAT",
            (
                agent_id,
                sample_agent_info.scaling_group,
                sample_agent_info.available_resource_slots,
            ),
        )

    @pytest.mark.asyncio
    async def test_handle_heartbeat_agent_revival(
        self,
        agent_service: AgentService,
        mock_agent_repository: AsyncMock,
        mock_agent_cache: MagicMock,
        mock_event_producer: AsyncMock,
        mock_hook_plugin_ctx: AsyncMock,
        sample_agent_info: AgentInfo,
    ) -> None:
        # Given
        agent_id = AgentId("agent-revival")
        action = HandleHeartbeatAction(
            agent_id=agent_id,
            agent_info=sample_agent_info,
        )

        upsert_result = UpsertResult(
            was_revived=True,  # Agent was revived
            need_resource_slot_update=False,
        )
        mock_agent_repository.sync_agent_heartbeat.return_value = upsert_result
        mock_agent_repository.sync_installed_images.return_value = None

        # When
        result = await agent_service.handle_heartbeat(action)

        # Then
        assert isinstance(result, HandleHeartbeatActionResult)
        assert result.agent_id == agent_id

        # Verify revival event was sent
        mock_event_producer.anycast_event.assert_called_once()
        call_args = mock_event_producer.anycast_event.call_args
        assert isinstance(call_args[0][0], AgentStartedEvent)
        assert call_args[0][0].reason == "revived"
        assert call_args[1]["source_override"] == agent_id

        # Verify cache update
        mock_agent_cache.update.assert_called_once_with(
            agent_id,
            sample_agent_info.addr,
            sample_agent_info.public_key,
        )

        # Verify hook notification
        mock_hook_plugin_ctx.notify.assert_called_once_with(
            "POST_AGENT_HEARTBEAT",
            (
                agent_id,
                sample_agent_info.scaling_group,
                sample_agent_info.available_resource_slots,
            ),
        )

    @pytest.mark.asyncio
    async def test_handle_heartbeat_new_agent(
        self,
        agent_service: AgentService,
        mock_agent_repository: AsyncMock,
        mock_agent_cache: MagicMock,
        mock_event_producer: AsyncMock,
        mock_hook_plugin_ctx: AsyncMock,
        sample_agent_info: AgentInfo,
    ) -> None:
        # Given
        agent_id = AgentId("agent-new")
        action = HandleHeartbeatAction(
            agent_id=agent_id,
            agent_info=sample_agent_info,
        )

        upsert_result = UpsertResult(
            was_revived=False,
            need_resource_slot_update=True,  # New agent
        )
        mock_agent_repository.sync_agent_heartbeat.return_value = upsert_result
        mock_agent_repository.sync_installed_images.return_value = None

        # When
        result = await agent_service.handle_heartbeat(action)

        # Then
        assert isinstance(result, HandleHeartbeatActionResult)
        assert result.agent_id == agent_id

        # Verify no revival event (new agents don't trigger revival)
        mock_event_producer.anycast_event.assert_not_called()

        # Verify all other operations still happen
        mock_agent_cache.update.assert_called_once()
        mock_agent_repository.sync_installed_images.assert_called_once()
        mock_hook_plugin_ctx.notify.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_heartbeat_with_resource_update(
        self,
        agent_service: AgentService,
        mock_agent_repository: AsyncMock,
        mock_agent_cache: MagicMock,
        mock_event_producer: AsyncMock,
        mock_hook_plugin_ctx: AsyncMock,
    ) -> None:
        # Given
        agent_id = AgentId("agent-resource-update")
        agent_info = AgentInfo(
            ip="192.168.1.100",
            version="24.12.0",
            scaling_group="gpu-cluster",
            available_resource_slots=ResourceSlot({
                SlotName("cpu"): "16",
                SlotName("mem"): "65536",
                SlotName("cuda.shares"): "8",  # New GPU resources
            }),
            slot_key_and_units={
                SlotName("cpu"): SlotTypes.COUNT,
                SlotName("mem"): SlotTypes.BYTES,
                SlotName("cuda.shares"): SlotTypes.COUNT,
            },
            addr="tcp://192.168.1.200:6001",
            public_key=PublicKey(b"gpu-node-key"),
            public_host="192.168.1.200",
            images=b"\x82\xc4\x00\x00",
            region="us-west-2",
            architecture="x86_64",
            compute_plugins={DeviceName("cpu"): {}},
            auto_terminate_abusing_kernel=False,
        )
        action = HandleHeartbeatAction(
            agent_id=agent_id,
            agent_info=agent_info,
        )

        upsert_result = UpsertResult(
            was_revived=False,
            need_resource_slot_update=True,  # Resources changed
        )
        mock_agent_repository.sync_agent_heartbeat.return_value = upsert_result
        mock_agent_repository.sync_installed_images.return_value = None

        # When
        result = await agent_service.handle_heartbeat(action)

        # Then
        assert isinstance(result, HandleHeartbeatActionResult)
        assert result.agent_id == agent_id

        # Verify repository handled the resource update
        mock_agent_repository.sync_agent_heartbeat.assert_called_once()
        call_args = mock_agent_repository.sync_agent_heartbeat.call_args[0]
        upsert_data = call_args[1]
        assert SlotName("cuda.shares") in upsert_data.resource_info.slot_key_and_units

        # Verify hook gets new resource slots
        mock_hook_plugin_ctx.notify.assert_called_once()
        hook_args = mock_hook_plugin_ctx.notify.call_args[0]
        assert hook_args[0] == "POST_AGENT_HEARTBEAT"
        assert hook_args[1][2] == agent_info.available_resource_slots

    @pytest.mark.asyncio
    async def test_handle_heartbeat_concurrent_heartbeats(
        self,
        agent_service: AgentService,
        mock_agent_repository: AsyncMock,
        mock_agent_cache: MagicMock,
        mock_event_producer: AsyncMock,
        mock_hook_plugin_ctx: AsyncMock,
        sample_agent_info: AgentInfo,
    ) -> None:
        # Given
        agents = [AgentId(f"agent-{i:03d}") for i in range(5)]
        actions = [
            HandleHeartbeatAction(agent_id=agent_id, agent_info=sample_agent_info)
            for agent_id in agents
        ]

        upsert_result = UpsertResult(
            was_revived=False,
            need_resource_slot_update=False,
        )
        mock_agent_repository.sync_agent_heartbeat.return_value = upsert_result
        mock_agent_repository.sync_installed_images.return_value = None

        # When - simulate concurrent heartbeats
        tasks = [agent_service.handle_heartbeat(action) for action in actions]
        results = await asyncio.gather(*tasks)

        # Then
        assert len(results) == 5
        for i, result in enumerate(results):
            assert isinstance(result, HandleHeartbeatActionResult)
            assert result.agent_id == agents[i]

        # Verify all operations were called for each agent
        assert mock_agent_repository.sync_agent_heartbeat.call_count == 5
        assert mock_agent_cache.update.call_count == 5
        assert mock_agent_repository.sync_installed_images.call_count == 5
        assert mock_hook_plugin_ctx.notify.call_count == 5


class TestWatcher:
    @pytest.fixture
    def agent_id(self) -> AgentId:
        return AgentId("test-agent-watcher")

    @pytest.fixture
    def _setup_http_mock(self, mock_etcd: AsyncMock):
        def _setup(agent_id: AgentId, status: int, data: dict | str):
            # Setup etcd
            mock_etcd.get.side_effect = lambda key: {
                f"nodes/agents/{agent_id}/ip": "192.168.1.100",
                f"nodes/agents/{agent_id}/watcher_port": "6099",
            }.get(key)

            # Setup HTTP response
            mock_response = AsyncMock()
            mock_response.status = status
            mock_response.ok = status // 100 == 2
            if isinstance(data, dict):
                mock_response.json = AsyncMock(return_value=data)
            else:
                mock_response.text = AsyncMock(return_value=data)
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            # Setup HTTP session
            mock_session = AsyncMock()
            mock_session.request = MagicMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)

            return mock_session, mock_response

        return _setup

    @pytest.fixture
    def watcher_service_ok(self, agent_service: AgentService, agent_id: AgentId, _setup_http_mock):
        mock_session, _ = _setup_http_mock(agent_id, HTTPStatus.OK, {"result": "ok"})

        with patch(
            "ai.backend.manager.services.agent.service.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            yield agent_service

    @pytest.fixture
    def watcher_service_ok_get(
        self, agent_service: AgentService, agent_id: AgentId, _setup_http_mock
    ):
        mock_session, _ = _setup_http_mock(
            agent_id,
            HTTPStatus.OK,
            {"agent-status": "active", "watcher-status": "active"},
        )

        with patch(
            "ai.backend.manager.services.agent.service.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            yield agent_service

    @pytest.fixture
    def watcher_service_forbidden(
        self, agent_service: AgentService, agent_id: AgentId, _setup_http_mock
    ):
        mock_session, _ = _setup_http_mock(agent_id, HTTPStatus.FORBIDDEN, "Invalid token")

        with patch(
            "ai.backend.manager.services.agent.service.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            yield agent_service

    @pytest.fixture
    def watcher_service_error(
        self, agent_service: AgentService, agent_id: AgentId, _setup_http_mock
    ):
        mock_session, _ = _setup_http_mock(
            agent_id, HTTPStatus.INTERNAL_SERVER_ERROR, "Systemctl command failed"
        )

        with patch(
            "ai.backend.manager.services.agent.service.aiohttp.ClientSession",
            return_value=mock_session,
        ):
            yield agent_service

    @pytest.mark.asyncio
    async def test_agent_start_success(
        self, watcher_service_ok: AgentService, agent_id: AgentId
    ) -> None:
        # When
        result = await watcher_service_ok.watcher_agent_start(
            WatcherAgentStartAction(agent_id=agent_id)
        )

        # Then
        assert result.data == {"result": "ok"}

    @pytest.mark.asyncio
    async def test_agent_stop_success(
        self, watcher_service_ok: AgentService, agent_id: AgentId
    ) -> None:
        # When
        result = await watcher_service_ok.watcher_agent_stop(
            WatcherAgentStopAction(agent_id=agent_id)
        )

        # Then
        assert result.data == {"result": "ok"}

    @pytest.mark.asyncio
    async def test_agent_restart_success(
        self, watcher_service_ok: AgentService, agent_id: AgentId
    ) -> None:
        # When
        result = await watcher_service_ok.watcher_agent_restart(
            WatcherAgentRestartAction(agent_id=agent_id)
        )

        # Then
        assert result.data == {"result": "ok"}

    @pytest.mark.asyncio
    async def test_get_status_success(
        self, watcher_service_ok_get: AgentService, agent_id: AgentId
    ) -> None:
        # When
        result = await watcher_service_ok_get.get_watcher_status(
            GetWatcherStatusAction(agent_id=agent_id)
        )

        # Then
        assert result.data["agent-status"] == "active"
        assert result.data["watcher-status"] == "active"

    # ==================== Error Tests ====================

    @pytest.mark.asyncio
    async def test_agent_start_forbidden(
        self, watcher_service_forbidden: AgentService, agent_id: AgentId
    ) -> None:
        # When/Then
        with pytest.raises(AgentWatcherResponseError) as exc_info:
            await watcher_service_forbidden.watcher_agent_start(
                WatcherAgentStartAction(agent_id=agent_id)
            )

        assert exc_info.value.status_code == HTTPStatus.FORBIDDEN
        assert "Agent watcher error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_agent_stop_internal_error(
        self, watcher_service_error: AgentService, agent_id: AgentId
    ) -> None:
        # When/Then
        with pytest.raises(AgentWatcherResponseError) as exc_info:
            await watcher_service_error.watcher_agent_stop(
                WatcherAgentStopAction(agent_id=agent_id)
            )

        assert exc_info.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert "Agent watcher error" in str(exc_info.value)
