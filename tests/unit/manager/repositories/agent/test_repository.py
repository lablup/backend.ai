"""
Tests for AgentRepository functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Mapping
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from dateutil.tz import tzutc

from ai.backend.common.auth import PublicKey
from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.data.agent.types import AgentInfo
from ai.backend.common.exception import AgentNotFound
from ai.backend.common.types import (
    AgentId,
    DeviceName,
    ResourceSlot,
    SlotName,
    SlotTypes,
    ValkeyTarget,
)
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.agent.types import AgentHeartbeatUpsert, AgentStatus
from ai.backend.manager.errors.resource import ScalingGroupNotFound
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.agent.repository import AgentRepository
from ai.backend.testutils.db import with_tables


class TestAgentRepositoryDB:
    """Test cases for AgentRepository with real database"""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created. TRUNCATE CASCADE handles cleanup."""
        async with with_tables(
            database_connection,
            [
                # FK dependency order: parents first
                DomainRow,
                ProjectResourcePolicyRow,
                UserResourcePolicyRow,
                KeyPairResourcePolicyRow,
                ScalingGroupRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                AgentRow,
                SessionRow,
                KernelRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def sample_agent_info(self) -> AgentInfo:
        """Create sample agent info for testing"""
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
            compute_plugins={
                DeviceName("cpu"): {"brand": "Intel", "model": "Core i7"},
            },
            addr="tcp://192.168.1.100:6001",
            public_key=PublicKey(b"test-public-key"),
            public_host="192.168.1.100",
            images=b"\x82\xc4\x00\x00",
            region="us-west-1",
            architecture="x86_64",
            auto_terminate_abusing_kernel=False,
        )

    @pytest.fixture
    def sample_agent_info_with_new_slots(self) -> AgentInfo:
        """Create sample agent info with additional slot types for testing resource slot updates"""
        return AgentInfo(
            ip="192.168.1.101",
            version="24.12.0",
            scaling_group="default",
            available_resource_slots=ResourceSlot({
                SlotName("cpu"): "8",
                SlotName("mem"): "32768",
                SlotName("cuda.shares"): "4",
                SlotName("rocm.device"): "2",
            }),
            slot_key_and_units={
                SlotName("cpu"): SlotTypes.COUNT,
                SlotName("mem"): SlotTypes.BYTES,
                SlotName("cuda.shares"): SlotTypes.COUNT,
                SlotName("rocm.device"): SlotTypes.COUNT,
            },
            compute_plugins={DeviceName("cpu"): {}},
            addr="tcp://192.168.1.101:6001",
            public_key=PublicKey(b"test-public-key-2"),
            public_host="192.168.1.101",
            images=b"\x82\xc4\x00\x00",
            region="us-east-1",
            architecture="x86_64",
            auto_terminate_abusing_kernel=False,
        )

    @pytest.fixture
    def mock_valkey_image(self) -> MagicMock:
        """Mock ValkeyImageClient"""
        return MagicMock(spec=ValkeyImageClient)

    @pytest.fixture
    def mock_valkey_live(self) -> MagicMock:
        """Mock ValkeyLiveClient"""
        mock = MagicMock(spec=ValkeyLiveClient)
        mock.update_agent_last_seen = AsyncMock()
        return mock

    @pytest.fixture
    def mock_valkey_stat(self) -> MagicMock:
        """Mock ValkeyStatClient"""
        return MagicMock(spec=ValkeyStatClient)

    @pytest.fixture
    def mock_config_provider(self) -> MagicMock:
        """Mock config provider for legacy etcd operations"""
        mock = MagicMock(spec=ManagerConfigProvider)
        mock.legacy_etcd_config_loader = AsyncMock()
        mock.legacy_etcd_config_loader.update_resource_slots = AsyncMock()
        return mock

    @pytest.fixture
    def agent_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        mock_valkey_image: MagicMock,
        mock_valkey_live: MagicMock,
        mock_valkey_stat: MagicMock,
        mock_config_provider: MagicMock,
    ) -> AgentRepository:
        """Create AgentRepository with real DB and mock Redis clients"""
        return AgentRepository(
            db=db_with_cleanup,
            valkey_image=mock_valkey_image,
            valkey_live=mock_valkey_live,
            valkey_stat=mock_valkey_stat,
            config_provider=mock_config_provider,
        )

    @pytest.fixture
    async def scaling_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create default scaling group in database"""
        name = "default"
        async with db_with_cleanup.begin_session() as db_sess:
            scaling_group = ScalingGroupRow(
                name=name,
                description="Test scaling group",
                is_active=True,
                is_public=True,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
                use_host_network=False,
            )
            db_sess.add(scaling_group)
        yield name

    @pytest.fixture
    async def alive_agent(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scaling_group: str,
    ) -> AsyncGenerator[AgentId, None]:
        """Create an alive agent in database"""
        agent_id = AgentId("agent-alive")
        async with db_with_cleanup.begin_session() as db_sess:
            agent = AgentRow(
                id=agent_id,
                status=AgentStatus.ALIVE,
                status_changed=datetime.now(tzutc()),
                region="us-west-1",
                scaling_group=scaling_group,
                available_slots=ResourceSlot({SlotName("cpu"): 8.0}),
                occupied_slots=ResourceSlot({}),
                addr="tcp://192.168.1.100:6001",
                first_contact=datetime.now(tzutc()),
                lost_at=None,
                public_host="192.168.1.100",
                public_key=PublicKey(b"test-public-key"),
                version="24.12.0",
                architecture="x86_64",
                compute_plugins={},
                schedulable=True,
                auto_terminate_abusing_kernel=False,
            )
            db_sess.add(agent)
        yield agent_id

    @pytest.fixture
    async def lost_agent(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scaling_group: str,
    ) -> AsyncGenerator[AgentId, None]:
        """Create a lost agent in database"""
        agent_id = AgentId("agent-lost")
        async with db_with_cleanup.begin_session() as db_sess:
            agent = AgentRow(
                id=agent_id,
                status=AgentStatus.LOST,
                status_changed=datetime.now(tzutc()),
                region="us-west-1",
                scaling_group=scaling_group,
                available_slots=ResourceSlot({SlotName("cpu"): 8.0}),
                occupied_slots=ResourceSlot({}),
                addr="tcp://192.168.1.100:6001",
                first_contact=datetime.now(tzutc()),
                lost_at=datetime.now(tzutc()),
                public_host="192.168.1.100",
                public_key=PublicKey(b"test-public-key"),
                version="24.12.0",
                architecture="x86_64",
                compute_plugins={},
                schedulable=True,
                auto_terminate_abusing_kernel=False,
            )
            db_sess.add(agent)
        yield agent_id

    # ==================== get_by_id tests ====================

    async def test_get_by_id_existing_agent(
        self,
        agent_repository: AgentRepository,
        alive_agent: AgentId,
    ) -> None:
        """Test getting an existing agent by ID"""
        result = await agent_repository.get_by_id(alive_agent)

        assert result.id == alive_agent
        assert result.status == AgentStatus.ALIVE
        assert result.scaling_group == "default"

    async def test_get_by_id_nonexistent_agent(
        self,
        agent_repository: AgentRepository,
    ) -> None:
        """Test getting a non-existent agent raises AgentNotFound"""
        with pytest.raises(AgentNotFound):
            await agent_repository.get_by_id(AgentId("nonexistent-agent"))

    # ==================== sync_agent_heartbeat tests ====================

    async def test_sync_agent_heartbeat_new_agent(
        self,
        agent_repository: AgentRepository,
        scaling_group: str,
        sample_agent_info: AgentInfo,
    ) -> None:
        """Test sync_agent_heartbeat creates a new agent"""
        agent_id = AgentId("agent-new")
        upsert_data = AgentHeartbeatUpsert.from_agent_info(
            agent_id=agent_id,
            agent_info=sample_agent_info,
            heartbeat_received=datetime.now(tzutc()),
        )

        result = await agent_repository.sync_agent_heartbeat(agent_id, upsert_data)

        assert result.was_revived is False
        assert result.need_resource_slot_update is True
        agent = await agent_repository.get_by_id(agent_id)
        assert agent.id == agent_id
        assert agent.status == AgentStatus.ALIVE

    async def test_sync_agent_heartbeat_existing_agent_alive(
        self,
        agent_repository: AgentRepository,
        alive_agent: AgentId,
        sample_agent_info: AgentInfo,
    ) -> None:
        """Test sync_agent_heartbeat updates an existing alive agent"""
        upsert_data = AgentHeartbeatUpsert.from_agent_info(
            agent_id=alive_agent,
            agent_info=sample_agent_info,
            heartbeat_received=datetime.now(tzutc()),
        )

        result = await agent_repository.sync_agent_heartbeat(alive_agent, upsert_data)

        assert result.was_revived is False

    async def test_sync_agent_heartbeat_revived_agent(
        self,
        agent_repository: AgentRepository,
        lost_agent: AgentId,
        sample_agent_info: AgentInfo,
    ) -> None:
        """Test sync_agent_heartbeat revives a previously lost agent"""
        upsert_data = AgentHeartbeatUpsert.from_agent_info(
            agent_id=lost_agent,
            agent_info=sample_agent_info,
            heartbeat_received=datetime.now(tzutc()),
        )

        result = await agent_repository.sync_agent_heartbeat(lost_agent, upsert_data)

        assert result.was_revived is True
        agent = await agent_repository.get_by_id(lost_agent)
        assert agent.status == AgentStatus.ALIVE

    async def test_sync_agent_heartbeat_scaling_group_not_found(
        self,
        agent_repository: AgentRepository,
        sample_agent_info: AgentInfo,
    ) -> None:
        """Test sync_agent_heartbeat raises ScalingGroupNotFound for non-existent scaling group"""
        agent_id = AgentId("agent-no-sgroup")
        upsert_data = AgentHeartbeatUpsert.from_agent_info(
            agent_id=agent_id,
            agent_info=sample_agent_info,
            heartbeat_received=datetime.now(tzutc()),
        )

        with pytest.raises(ScalingGroupNotFound):
            await agent_repository.sync_agent_heartbeat(agent_id, upsert_data)

    async def test_sync_agent_heartbeat_with_new_resource_slots(
        self,
        agent_repository: AgentRepository,
        scaling_group: str,
        sample_agent_info_with_new_slots: AgentInfo,
        mock_config_provider: MagicMock,
    ) -> None:
        """Test sync_agent_heartbeat updates resource slots when new slot types are added"""
        agent_id = AgentId("agent-new-slots")
        upsert_data = AgentHeartbeatUpsert.from_agent_info(
            agent_id=agent_id,
            agent_info=sample_agent_info_with_new_slots,
            heartbeat_received=datetime.now(tzutc()),
        )

        result = await agent_repository.sync_agent_heartbeat(agent_id, upsert_data)

        assert result.need_resource_slot_update is True
        mock_config_provider.legacy_etcd_config_loader.update_resource_slots.assert_called_once()


class TestAgentRepositoryCache:
    """Test cases for AgentRepository cache operations with real Redis"""

    @pytest.fixture
    async def valkey_image_client(
        self,
        redis_container: tuple[str, tuple[str, int]],
    ) -> AsyncGenerator[ValkeyImageClient, None]:
        """Create ValkeyImageClient with real Redis container"""
        _, redis_addr = redis_container

        valkey_target = ValkeyTarget(
            addr=f"{redis_addr[0]}:{redis_addr[1]}",
        )

        client = await ValkeyImageClient.create(
            valkey_target=valkey_target,
            db_id=1,
            human_readable_name="test-valkey-image",
        )

        try:
            yield client
        finally:
            await client.close()

    @pytest.fixture
    async def valkey_live_client(
        self,
        redis_container: tuple[str, tuple[str, int]],
    ) -> AsyncGenerator[ValkeyLiveClient, None]:
        """Create ValkeyLiveClient with real Redis container"""
        _, redis_addr = redis_container

        valkey_target = ValkeyTarget(
            addr=f"{redis_addr[0]}:{redis_addr[1]}",
        )

        client = await ValkeyLiveClient.create(
            valkey_target=valkey_target,
            db_id=2,
            human_readable_name="test-valkey-live",
        )

        try:
            yield client
        finally:
            await client.close()

    @pytest.fixture
    async def valkey_stat_client(
        self,
        redis_container: tuple[str, tuple[str, int]],
    ) -> AsyncGenerator[ValkeyStatClient, None]:
        """Create ValkeyStatClient with real Redis container"""
        _, redis_addr = redis_container

        valkey_target = ValkeyTarget(
            addr=f"{redis_addr[0]}:{redis_addr[1]}",
        )

        client = await ValkeyStatClient.create(
            valkey_target=valkey_target,
            db_id=3,
            human_readable_name="test-valkey-stat",
        )

        try:
            yield client
        finally:
            await client.close()

    @pytest.fixture
    def mock_config_provider(self) -> MagicMock:
        """Mock config provider for legacy etcd operations"""
        mock = MagicMock(spec=ManagerConfigProvider)
        mock.legacy_etcd_config_loader = AsyncMock()
        mock.legacy_etcd_config_loader.update_resource_slots = AsyncMock()
        return mock

    @pytest.fixture
    def mock_database_engine(self) -> MagicMock:
        """Mock database engine - not needed for cache-only tests"""
        return MagicMock(spec=ExtendedAsyncSAEngine)

    @pytest.fixture
    async def agent_repository(
        self,
        mock_database_engine: MagicMock,
        valkey_image_client: ValkeyImageClient,
        valkey_live_client: ValkeyLiveClient,
        valkey_stat_client: ValkeyStatClient,
        mock_config_provider: MagicMock,
    ) -> AsyncGenerator[AgentRepository, None]:
        """Create AgentRepository with real Redis clients and mock database"""
        repo = AgentRepository(
            db=mock_database_engine,
            valkey_image=valkey_image_client,
            valkey_live=valkey_live_client,
            valkey_stat=valkey_stat_client,
            config_provider=mock_config_provider,
        )
        yield repo

    async def test_update_gpu_alloc_map(
        self,
        agent_repository: AgentRepository,
        valkey_stat_client: ValkeyStatClient,
    ) -> None:
        """Test GPU allocation map update is stored in cache"""
        agent_id = AgentId("agent-001")
        alloc_map: Mapping[str, Any] = {
            "cuda:0": {"session_id": "sess-001"},
            "cuda:1": {"session_id": "sess-002"},
        }

        await agent_repository.update_gpu_alloc_map(agent_id, alloc_map)

        stored_map = await valkey_stat_client.get_gpu_allocation_map(str(agent_id))
        assert stored_map == alloc_map
