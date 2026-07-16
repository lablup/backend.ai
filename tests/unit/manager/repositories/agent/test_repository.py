"""
Tests for AgentRepository functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Mapping
from copy import copy
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc

from ai.backend.common.auth import PublicKey
from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.data.agent.types import AgentInfo
from ai.backend.common.exception import AgentNotFound
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import (
    AgentId,
    ClusterMode,
    DeviceName,
    ResourceSlot,
    SessionResult,
    SessionTypes,
    SlotName,
    SlotTypes,
    ValkeyTarget,
)
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.agent.types import AgentHeartbeatUpsert, AgentStatus
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.errors.resource import UnresolvableResourceGroup
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy import DeploymentAutoScalingPolicyRow
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.resource_slot import AgentResourceRow, ResourceSlotTypeRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.runtime_variant import RuntimeVariantRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.agent.db_source.db_source import AgentDBSource
from ai.backend.manager.repositories.agent.repository import AgentRepository
from ai.backend.manager.repositories.base.pagination import OffsetPagination
from ai.backend.manager.repositories.base.querier import BatchQuerier
from ai.backend.testutils.db import with_tables


@dataclass
class ScalingGroupFixtureData:
    """Data from scaling_group fixture"""

    name: str
    id: ResourceGroupID


@dataclass
class AgentFixtureData:
    """Data from agent fixtures (alive_agent, lost_agent)"""

    agent_id: AgentId
    scaling_group: str


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
                # FK dependency order: parents before children
                DomainRow,
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                RoleRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                ContainerRegistryRow,
                ImageRow,
                VFolderRow,
                EndpointRow,
                DeploymentPolicyRow,
                DeploymentAutoScalingPolicyRow,
                RuntimeVariantRow,
                DeploymentRevisionPresetRow,
                DeploymentRevisionRow,
                SessionRow,
                AgentRow,
                KernelRow,
                ReplicaGroupRow,
                RoutingRow,
                ResourcePresetRow,
                ResourceSlotTypeRow,
                AgentResourceRow,
            ],
        ):
            # Seed default resource slot types (FK target for agent_resources)
            async with database_connection.begin_session() as db_sess:
                for slot_name, slot_type in [
                    ("cpu", "count"),
                    ("mem", "bytes"),
                    ("cuda.shares", "count"),
                    ("rocm.device", "count"),
                ]:
                    db_sess.add(
                        ResourceSlotTypeRow(slot_name=slot_name, slot_type=slot_type, rank=0)
                    )
            yield database_connection

    @pytest.fixture
    def sample_agent_info(self, scaling_group: ScalingGroupFixtureData) -> AgentInfo:
        """Create sample agent info for testing"""
        return AgentInfo(
            ip="192.168.1.100",
            version="24.12.0",
            scaling_group=scaling_group.name,
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
    def sample_agent_info_with_new_slots(self, scaling_group: ScalingGroupFixtureData) -> AgentInfo:
        """Create sample agent info with additional slot types for testing resource slot updates"""
        return AgentInfo(
            ip="192.168.1.101",
            version="24.12.0",
            scaling_group=scaling_group.name,
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
    ) -> AsyncGenerator[ScalingGroupFixtureData, None]:
        """Create default scaling group in database"""
        name = str(uuid4())
        scaling_group_id = ResourceGroupID(uuid4())
        async with db_with_cleanup.begin_session() as db_sess:
            scaling_group = ScalingGroupRow(
                id=scaling_group_id,
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
        yield ScalingGroupFixtureData(name=name, id=scaling_group_id)

    @pytest.fixture
    async def alive_agent(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scaling_group: ScalingGroupFixtureData,
    ) -> AsyncGenerator[AgentFixtureData, None]:
        """Create an alive agent in database"""
        agent_id = AgentId(str(uuid4()))
        async with db_with_cleanup.begin_session() as db_sess:
            agent = AgentRow(
                id=agent_id,
                status=AgentStatus.ALIVE,
                status_changed=datetime.now(tzutc()),
                region="us-west-1",
                scaling_group=scaling_group.name,
                resource_group_id=scaling_group.id,
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
        yield AgentFixtureData(agent_id=agent_id, scaling_group=scaling_group.name)

    @pytest.fixture
    async def lost_agent(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scaling_group: ScalingGroupFixtureData,
    ) -> AsyncGenerator[AgentFixtureData, None]:
        """Create a lost agent in database"""
        agent_id = AgentId(str(uuid4()))
        async with db_with_cleanup.begin_session() as db_sess:
            agent = AgentRow(
                id=agent_id,
                status=AgentStatus.LOST,
                status_changed=datetime.now(tzutc()),
                region="us-west-1",
                scaling_group=scaling_group.name,
                resource_group_id=scaling_group.id,
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
        yield AgentFixtureData(agent_id=agent_id, scaling_group=scaling_group.name)

    # ==================== get_by_id tests ====================

    async def test_get_by_id_existing_agent(
        self,
        agent_repository: AgentRepository,
        alive_agent: AgentFixtureData,
    ) -> None:
        """Test getting an existing agent by ID"""
        result = await agent_repository.get_by_id(alive_agent.agent_id)

        assert result.id == alive_agent.agent_id
        assert result.status == AgentStatus.ALIVE
        assert result.scaling_group == alive_agent.scaling_group

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
        sample_agent_info: AgentInfo,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scaling_group: ScalingGroupFixtureData,
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
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            resource_group_id = await db_sess.scalar(
                sa.select(AgentRow.resource_group_id).where(AgentRow.id == agent_id)
            )
        assert resource_group_id == scaling_group.id

    async def test_sync_agent_heartbeat_existing_agent_alive(
        self,
        agent_repository: AgentRepository,
        alive_agent: AgentFixtureData,
        sample_agent_info: AgentInfo,
    ) -> None:
        """Test sync_agent_heartbeat updates an existing alive agent"""
        upsert_data = AgentHeartbeatUpsert.from_agent_info(
            agent_id=alive_agent.agent_id,
            agent_info=sample_agent_info,
            heartbeat_received=datetime.now(tzutc()),
        )

        result = await agent_repository.sync_agent_heartbeat(alive_agent.agent_id, upsert_data)

        assert result.was_revived is False

    async def test_sync_agent_heartbeat_revived_agent(
        self,
        agent_repository: AgentRepository,
        lost_agent: AgentFixtureData,
        sample_agent_info: AgentInfo,
    ) -> None:
        """Test sync_agent_heartbeat revives a previously lost agent"""
        upsert_data = AgentHeartbeatUpsert.from_agent_info(
            agent_id=lost_agent.agent_id,
            agent_info=sample_agent_info,
            heartbeat_received=datetime.now(tzutc()),
        )

        result = await agent_repository.sync_agent_heartbeat(lost_agent.agent_id, upsert_data)

        assert result.was_revived is True
        agent = await agent_repository.get_by_id(lost_agent.agent_id)
        assert agent.status == AgentStatus.ALIVE

    async def test_sync_agent_heartbeat_scaling_group_change_is_ignored(
        self,
        agent_repository: AgentRepository,
        alive_agent: AgentFixtureData,
        scaling_group: ScalingGroupFixtureData,
        sample_agent_info: AgentInfo,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """The DB is authoritative: a heartbeat reporting a different scaling group must not
        change the agent's group columns."""
        new_sgroup_name = str(uuid4())
        new_sgroup_id = ResourceGroupID(uuid4())
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                ScalingGroupRow(
                    id=new_sgroup_id,
                    name=new_sgroup_name,
                    description="Second scaling group",
                    is_active=True,
                    is_public=True,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    scheduler_opts=ScalingGroupOpts(),
                    use_host_network=False,
                )
            )
        moved_agent_info = sample_agent_info.model_copy(update={"scaling_group": new_sgroup_name})
        upsert_data = AgentHeartbeatUpsert.from_agent_info(
            agent_id=alive_agent.agent_id,
            agent_info=moved_agent_info,
            heartbeat_received=datetime.now(tzutc()),
        )

        await agent_repository.sync_agent_heartbeat(alive_agent.agent_id, upsert_data)

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            row = (
                await db_sess.execute(
                    sa.select(AgentRow.scaling_group, AgentRow.resource_group_id).where(
                        AgentRow.id == alive_agent.agent_id
                    )
                )
            ).one()
        assert row.scaling_group == scaling_group.name
        assert row.resource_group_id == scaling_group.id

    async def test_sync_agent_heartbeat_unresolvable_group_no_default(
        self,
        agent_repository: AgentRepository,
    ) -> None:
        """A new agent whose reported group does not exist and with no default group configured
        fails registration with UnresolvableResourceGroup."""
        agent_id = AgentId("agent-no-sgroup")
        agent_info_with_nonexistent_sg = AgentInfo(
            ip="192.168.1.100",
            version="24.12.0",
            scaling_group="nonexistent-scaling-group",
            available_resource_slots=ResourceSlot({
                SlotName("cpu"): "8",
                SlotName("mem"): "32768",
            }),
            slot_key_and_units={
                SlotName("cpu"): SlotTypes.COUNT,
                SlotName("mem"): SlotTypes.BYTES,
            },
            compute_plugins={DeviceName("cpu"): {}},
            addr="tcp://192.168.1.100:6001",
            public_key=PublicKey(b"test-public-key"),
            public_host="192.168.1.100",
            images=b"\x82\xc4\x00\x00",
            region="us-west-1",
            architecture="x86_64",
            auto_terminate_abusing_kernel=False,
        )
        upsert_data = AgentHeartbeatUpsert.from_agent_info(
            agent_id=agent_id,
            agent_info=agent_info_with_nonexistent_sg,
            heartbeat_received=datetime.now(tzutc()),
        )

        with pytest.raises(UnresolvableResourceGroup):
            await agent_repository.sync_agent_heartbeat(agent_id, upsert_data)

    async def test_sync_agent_heartbeat_with_new_resource_slots(
        self,
        agent_repository: AgentRepository,
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

    # ==================== upsert_agent_with_state tests ====================

    @pytest.fixture
    def agent_db_source(self, db_with_cleanup: ExtendedAsyncSAEngine) -> AgentDBSource:
        """AgentDBSource backed by the real test database."""
        return AgentDBSource(db_with_cleanup)

    @pytest.fixture
    async def default_scaling_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ScalingGroupFixtureData, None]:
        """Create a scaling group marked as the default (is_default=True)."""
        name = str(uuid4())
        scaling_group_id = ResourceGroupID(uuid4())
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                ScalingGroupRow(
                    id=scaling_group_id,
                    name=name,
                    description="Default scaling group",
                    is_active=True,
                    is_public=True,
                    is_default=True,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    scheduler_opts=ScalingGroupOpts(),
                    use_host_network=False,
                )
            )
        yield ScalingGroupFixtureData(name=name, id=scaling_group_id)

    async def test_upsert_new_agent_inserts_with_resolved_group(
        self,
        agent_db_source: AgentDBSource,
        scaling_group: ScalingGroupFixtureData,
        sample_agent_info: AgentInfo,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """A new agent (no existing row) is inserted with the resolved resource group."""
        agent_id = AgentId("upsert-new-resolvable")
        upsert_data = AgentHeartbeatUpsert.from_agent_info(
            agent_id=agent_id,
            agent_info=sample_agent_info,
            heartbeat_received=datetime.now(tzutc()),
        )

        result = await agent_db_source.upsert_agent_with_state(upsert_data)

        assert result.was_revived is False
        assert result.need_resource_slot_update is True
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            row = (
                await db_sess.execute(
                    sa.select(
                        AgentRow.status, AgentRow.scaling_group, AgentRow.resource_group_id
                    ).where(AgentRow.id == agent_id)
                )
            ).one()
        assert row.status == AgentStatus.ALIVE
        assert row.scaling_group == scaling_group.name
        assert row.resource_group_id == scaling_group.id

    async def test_upsert_new_agent_prefers_named_group_over_default(
        self,
        agent_db_source: AgentDBSource,
        scaling_group: ScalingGroupFixtureData,
        default_scaling_group: ScalingGroupFixtureData,
        sample_agent_info: AgentInfo,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """With a default group present, a resolvable reported name still wins over the default."""
        agent_id = AgentId("upsert-new-named-over-default")
        # sample_agent_info reports scaling_group.name, which exists and is not the default.
        upsert_data = AgentHeartbeatUpsert.from_agent_info(
            agent_id=agent_id,
            agent_info=sample_agent_info,
            heartbeat_received=datetime.now(tzutc()),
        )

        await agent_db_source.upsert_agent_with_state(upsert_data)

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            row = (
                await db_sess.execute(
                    sa.select(AgentRow.scaling_group, AgentRow.resource_group_id).where(
                        AgentRow.id == agent_id
                    )
                )
            ).one()
        assert row.scaling_group == scaling_group.name
        assert row.resource_group_id == scaling_group.id
        assert row.resource_group_id != default_scaling_group.id

    async def test_upsert_new_agent_unresolvable_name_falls_back_to_default(
        self,
        agent_db_source: AgentDBSource,
        default_scaling_group: ScalingGroupFixtureData,
        sample_agent_info: AgentInfo,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """A new agent reporting an unknown group is registered into the default group."""
        agent_id = AgentId("upsert-new-fallback")
        info = sample_agent_info.model_copy(update={"scaling_group": f"ghost-{uuid4()}"})
        upsert_data = AgentHeartbeatUpsert.from_agent_info(
            agent_id=agent_id,
            agent_info=info,
            heartbeat_received=datetime.now(tzutc()),
        )

        await agent_db_source.upsert_agent_with_state(upsert_data)

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            row = (
                await db_sess.execute(
                    sa.select(AgentRow.scaling_group, AgentRow.resource_group_id).where(
                        AgentRow.id == agent_id
                    )
                )
            ).one()
        assert row.scaling_group == default_scaling_group.name
        assert row.resource_group_id == default_scaling_group.id

    async def test_upsert_new_agent_empty_name_uses_default(
        self,
        agent_db_source: AgentDBSource,
        default_scaling_group: ScalingGroupFixtureData,
        sample_agent_info: AgentInfo,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """A new agent reporting no group name (empty) is registered into the default group."""
        agent_id = AgentId("upsert-new-empty")
        info = sample_agent_info.model_copy(update={"scaling_group": ""})
        upsert_data = AgentHeartbeatUpsert.from_agent_info(
            agent_id=agent_id,
            agent_info=info,
            heartbeat_received=datetime.now(tzutc()),
        )

        await agent_db_source.upsert_agent_with_state(upsert_data)

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            resource_group_id = await db_sess.scalar(
                sa.select(AgentRow.resource_group_id).where(AgentRow.id == agent_id)
            )
        assert resource_group_id == default_scaling_group.id

    async def test_upsert_new_agent_unresolvable_name_no_default_raises(
        self,
        agent_db_source: AgentDBSource,
        scaling_group: ScalingGroupFixtureData,
        sample_agent_info: AgentInfo,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Registration fails when the reported group is unknown and no default group exists."""
        agent_id = AgentId("upsert-new-noresolve")
        info = sample_agent_info.model_copy(update={"scaling_group": f"ghost-{uuid4()}"})
        upsert_data = AgentHeartbeatUpsert.from_agent_info(
            agent_id=agent_id,
            agent_info=info,
            heartbeat_received=datetime.now(tzutc()),
        )

        with pytest.raises(UnresolvableResourceGroup):
            await agent_db_source.upsert_agent_with_state(upsert_data)

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            exists = await db_sess.scalar(sa.select(AgentRow.id).where(AgentRow.id == agent_id))
        assert exists is None

    async def test_upsert_existing_agent_keeps_group_on_different_report(
        self,
        agent_db_source: AgentDBSource,
        alive_agent: AgentFixtureData,
        scaling_group: ScalingGroupFixtureData,
        sample_agent_info: AgentInfo,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """An existing agent reporting a different (resolvable) group keeps its DB group."""
        other_name = str(uuid4())
        other_id = ResourceGroupID(uuid4())
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                ScalingGroupRow(
                    id=other_id,
                    name=other_name,
                    description="Another scaling group",
                    is_active=True,
                    is_public=True,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    scheduler_opts=ScalingGroupOpts(),
                    use_host_network=False,
                )
            )
        info = sample_agent_info.model_copy(update={"scaling_group": other_name})
        upsert_data = AgentHeartbeatUpsert.from_agent_info(
            agent_id=alive_agent.agent_id,
            agent_info=info,
            heartbeat_received=datetime.now(tzutc()),
        )

        result = await agent_db_source.upsert_agent_with_state(upsert_data)

        assert result.was_revived is False
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            row = (
                await db_sess.execute(
                    sa.select(AgentRow.scaling_group, AgentRow.resource_group_id).where(
                        AgentRow.id == alive_agent.agent_id
                    )
                )
            ).one()
        assert row.scaling_group == scaling_group.name
        assert row.resource_group_id == scaling_group.id

    async def test_upsert_revived_agent_keeps_group(
        self,
        agent_db_source: AgentDBSource,
        lost_agent: AgentFixtureData,
        scaling_group: ScalingGroupFixtureData,
        sample_agent_info: AgentInfo,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """A redeploy hits the UPDATE path: the lost agent is revived and its group is unchanged."""
        upsert_data = AgentHeartbeatUpsert.from_agent_info(
            agent_id=lost_agent.agent_id,
            agent_info=sample_agent_info,
            heartbeat_received=datetime.now(tzutc()),
        )

        result = await agent_db_source.upsert_agent_with_state(upsert_data)

        assert result.was_revived is True
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            row = (
                await db_sess.execute(
                    sa.select(
                        AgentRow.status, AgentRow.scaling_group, AgentRow.resource_group_id
                    ).where(AgentRow.id == lost_agent.agent_id)
                )
            ).one()
        assert row.status == AgentStatus.ALIVE
        assert row.scaling_group == scaling_group.name
        assert row.resource_group_id == scaling_group.id

    async def test_upsert_existing_agent_unresolvable_report_keeps_group(
        self,
        agent_db_source: AgentDBSource,
        alive_agent: AgentFixtureData,
        scaling_group: ScalingGroupFixtureData,
        default_scaling_group: ScalingGroupFixtureData,
        sample_agent_info: AgentInfo,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """An existing agent reporting an unknown group is not moved to the default group."""
        info = sample_agent_info.model_copy(update={"scaling_group": f"ghost-{uuid4()}"})
        upsert_data = AgentHeartbeatUpsert.from_agent_info(
            agent_id=alive_agent.agent_id,
            agent_info=info,
            heartbeat_received=datetime.now(tzutc()),
        )

        await agent_db_source.upsert_agent_with_state(upsert_data)

        async with db_with_cleanup.begin_readonly_session() as db_sess:
            row = (
                await db_sess.execute(
                    sa.select(AgentRow.scaling_group, AgentRow.resource_group_id).where(
                        AgentRow.id == alive_agent.agent_id
                    )
                )
            ).one()
        assert row.scaling_group == scaling_group.name
        assert row.resource_group_id == scaling_group.id

    async def test_upsert_existing_agent_unresolvable_report_no_default_still_updates(
        self,
        agent_db_source: AgentDBSource,
        alive_agent: AgentFixtureData,
        scaling_group: ScalingGroupFixtureData,
        sample_agent_info: AgentInfo,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """An existing agent reporting an unknown group with no default group must not fail its
        heartbeat: status/resources still update and the group is left unchanged."""
        new_addr = "tcp://10.0.0.9:6001"
        info = sample_agent_info.model_copy(
            update={"scaling_group": f"ghost-{uuid4()}", "addr": new_addr}
        )
        upsert_data = AgentHeartbeatUpsert.from_agent_info(
            agent_id=alive_agent.agent_id,
            agent_info=info,
            heartbeat_received=datetime.now(tzutc()),
        )

        result = await agent_db_source.upsert_agent_with_state(upsert_data)

        assert result.was_revived is False
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            row = (
                await db_sess.execute(
                    sa.select(
                        AgentRow.status,
                        AgentRow.addr,
                        AgentRow.scaling_group,
                        AgentRow.resource_group_id,
                    ).where(AgentRow.id == alive_agent.agent_id)
                )
            ).one()
        assert row.status == AgentStatus.ALIVE
        assert row.addr == new_addr  # the heartbeat update actually ran
        assert row.scaling_group == scaling_group.name  # group unchanged
        assert row.resource_group_id == scaling_group.id


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
            "GPU-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee": "0.50",
            "GPU-11111111-2222-3333-4444-555555555555": "1.00",
        }

        await agent_repository.update_gpu_alloc_map(agent_id, alloc_map)

        stored_map = await valkey_stat_client.get_gpu_allocation_map(str(agent_id))
        assert stored_map is not None
        assert stored_map == {
            "GPU-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee": Decimal("0.50"),
            "GPU-11111111-2222-3333-4444-555555555555": Decimal("1.00"),
        }


@dataclass
class KernelFilteringTestCase:
    """Test case for kernel filtering validation via actual_occupied_slots"""

    test_id: str
    agent_id: AgentId
    occupied_kernel_count: int
    non_occupied_kernel_count: int
    cpu_per_kernel: Decimal
    expected_actual_occupied_cpu: Decimal


class TestAgentDBSourceKernelFiltering:
    """Test kernel filtering with with_loader_criteria at db_source level"""

    @pytest.fixture
    async def db_with_tables(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables for kernel filtering tests"""
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                RoleRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                ContainerRegistryRow,
                ImageRow,
                VFolderRow,
                EndpointRow,
                DeploymentPolicyRow,
                DeploymentAutoScalingPolicyRow,
                RuntimeVariantRow,
                DeploymentRevisionPresetRow,
                DeploymentRevisionRow,
                SessionRow,
                AgentRow,
                KernelRow,
                ReplicaGroupRow,
                RoutingRow,
                ResourcePresetRow,
                ResourceSlotTypeRow,
                AgentResourceRow,
            ],
        ):
            # Seed default resource slot types
            async with database_connection.begin_session() as db_sess:
                db_sess.add(ResourceSlotTypeRow(slot_name="cpu", slot_type="count", rank=0))
            yield database_connection

    @pytest.fixture
    def test_domain_id(self) -> DomainID:
        return DomainID(uuid4())

    @pytest.fixture
    def test_scaling_group_id(self) -> ResourceGroupID:
        return ResourceGroupID(uuid4())

    @pytest.fixture
    async def test_domain(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
        test_domain_id: DomainID,
    ) -> AsyncGenerator[str, None]:
        """Create default domain"""
        domain_name = str(uuid4())
        async with db_with_tables.begin_session() as db_sess:
            domain = DomainRow(
                id=test_domain_id,
                name=domain_name,
                description="Test domain",
                is_active=True,
                total_resource_slots=ResourceSlot({}),
            )
            db_sess.add(domain)
        yield domain_name

    @pytest.fixture
    async def test_resource_policy(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create default project resource policy"""
        policy_name = str(uuid4())
        async with db_with_tables.begin_session() as db_sess:
            policy = ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_network_count=10,
            )
            db_sess.add(policy)
        yield policy_name

    @pytest.fixture
    async def test_group(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
        test_domain: str,
        test_resource_policy: str,
    ) -> AsyncGenerator[tuple[str, str], None]:
        """Create default group"""
        group_id = uuid4()
        async with db_with_tables.begin_session() as db_sess:
            group = GroupRow(
                id=group_id,
                name="default-group",
                domain_name=test_domain,
                total_resource_slots=ResourceSlot({}),
                integration_id=None,
                resource_policy=test_resource_policy,
            )
            db_sess.add(group)
        yield (str(group_id), test_domain)

    @pytest.fixture
    async def scaling_group(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
        test_scaling_group_id: ResourceGroupID,
    ) -> AsyncGenerator[str, None]:
        """Create default scaling group"""
        name = str(uuid4())
        async with db_with_tables.begin_session() as db_sess:
            scaling_group = ScalingGroupRow(
                id=test_scaling_group_id,
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
    async def agent_with_kernels(
        self,
        request: pytest.FixtureRequest,
        db_with_tables: ExtendedAsyncSAEngine,
        test_group: tuple[str, str],
        test_domain_id: DomainID,
        scaling_group: str,
        test_scaling_group_id: ResourceGroupID,
    ) -> AsyncGenerator[KernelFilteringTestCase, None]:
        """Create ONE agent with kernels based on the test case from indirect parametrization"""
        test_case: KernelFilteringTestCase = request.param
        group_id_str, domain_name = test_group

        # Generate random IDs and values for this test execution
        random_suffix = uuid4().hex[:8]
        actual_agent_id = AgentId(f"{test_case.agent_id}-{random_suffix}")
        random_ip_suffix = uuid4().int % 256  # Random IP octet (0-255)
        random_ip = f"192.168.1.{random_ip_suffix}"
        session_id = uuid4()
        session_name = f"test-session-{uuid4().hex[:12]}"

        async with db_with_tables.begin_session() as db_sess:
            # Create agent
            agent = AgentRow(
                id=actual_agent_id,
                status=AgentStatus.ALIVE,
                status_changed=datetime.now(tzutc()),
                region="us-west-1",
                scaling_group=scaling_group,
                resource_group_id=test_scaling_group_id,
                available_slots=ResourceSlot({SlotName("cpu"): 16.0}),
                occupied_slots=ResourceSlot({}),
                addr=f"tcp://{random_ip}:6001",
                first_contact=datetime.now(tzutc()),
                lost_at=None,
                public_host=random_ip,
                public_key=PublicKey(f"test-key-{random_suffix}".encode()),
                version="24.12.0",
                architecture="x86_64",
                compute_plugins={},
                schedulable=True,
                auto_terminate_abusing_kernel=False,
            )
            db_sess.add(agent)
            await db_sess.flush()

            # Seed AgentResourceRow with expected occupied value
            expected_used = test_case.cpu_per_kernel * test_case.occupied_kernel_count
            db_sess.add(
                AgentResourceRow(
                    agent_id=actual_agent_id,
                    slot_name="cpu",
                    capacity=Decimal("16"),
                    used=expected_used,
                )
            )
            await db_sess.flush()

            # Create session for all kernels
            session = SessionRow(
                id=session_id,
                name=session_name,
                session_type=SessionTypes.INTERACTIVE,
                domain_id=test_domain_id,
                domain_name=domain_name,
                group_id=UUID(group_id_str),
                resource_group_id=test_scaling_group_id,
                scaling_group_name=scaling_group,
                status=SessionStatus.RUNNING,
                status_info="test",
                cluster_mode=ClusterMode.SINGLE_NODE,
                requested_slots=ResourceSlot({SlotName("cpu"): 16.0}),
                created_at=datetime.now(tzutc()),
                images=["python:3.11"],
                vfolder_mounts=[],
                environ={},
                result=SessionResult.UNDEFINED,
            )
            db_sess.add(session)
            await db_sess.flush()

            # Create resource-occupied kernels
            # Only RUNNING and TERMINATING are considered resource-occupied
            occupied_statuses = [
                KernelStatus.RUNNING,
                KernelStatus.TERMINATING,
            ]
            for i in range(test_case.occupied_kernel_count):
                status = occupied_statuses[i % len(occupied_statuses)]
                kernel = KernelRow(
                    id=uuid4(),
                    session_id=session_id,
                    agent=actual_agent_id,
                    agent_addr=f"{random_ip}:6001",
                    scaling_group=scaling_group,
                    resource_group_id=test_scaling_group_id,
                    cluster_idx=i,
                    cluster_role="main",
                    cluster_hostname=f"main{i}-{uuid4().hex[:6]}",
                    image="python:3.11",
                    architecture="x86_64",
                    registry="docker.io",
                    container_id=f"container-{uuid4().hex[:8]}",
                    status=status,
                    occupied_slots=ResourceSlot({"cpu": Decimal(str(test_case.cpu_per_kernel))}),
                    requested_slots=ResourceSlot({"cpu": Decimal(str(test_case.cpu_per_kernel))}),
                    domain_name=domain_name,
                    group_id=UUID(group_id_str),
                    user_uuid=uuid4(),
                    access_key="AKTEST" + uuid4().hex[:12],
                    environ={},
                    mounts=[],
                    vfolder_mounts=[],
                    preopen_ports=[],
                    repl_in_port=2001 + i * 4,
                    repl_out_port=2002 + i * 4,
                    stdin_port=2003 + i * 4,
                    stdout_port=2004 + i * 4,
                )
                db_sess.add(kernel)

            # Create non-occupied kernels
            non_occupied_statuses = [
                KernelStatus.TERMINATED,
                KernelStatus.CANCELLED,
            ]
            for i in range(test_case.non_occupied_kernel_count):
                status = non_occupied_statuses[i % len(non_occupied_statuses)]
                kernel = KernelRow(
                    id=uuid4(),
                    session_id=session_id,
                    agent=actual_agent_id,
                    agent_addr=f"{random_ip}:6001",
                    scaling_group=scaling_group,
                    resource_group_id=test_scaling_group_id,
                    cluster_idx=test_case.occupied_kernel_count + i,
                    cluster_role="main",
                    cluster_hostname=f"main{test_case.occupied_kernel_count + i}-{uuid4().hex[:6]}",
                    image="python:3.11",
                    architecture="x86_64",
                    registry="docker.io",
                    container_id=f"container-{uuid4().hex[:8]}",
                    status=status,
                    occupied_slots=ResourceSlot({"cpu": Decimal(str(test_case.cpu_per_kernel))}),
                    requested_slots=ResourceSlot({"cpu": Decimal(str(test_case.cpu_per_kernel))}),
                    domain_name=domain_name,
                    group_id=UUID(group_id_str),
                    user_uuid=uuid4(),
                    access_key="AKTEST" + uuid4().hex[:12],
                    environ={},
                    mounts=[],
                    vfolder_mounts=[],
                    preopen_ports=[],
                    repl_in_port=2001 + (test_case.occupied_kernel_count + i) * 4,
                    repl_out_port=2002 + (test_case.occupied_kernel_count + i) * 4,
                    stdin_port=2003 + (test_case.occupied_kernel_count + i) * 4,
                    stdout_port=2004 + (test_case.occupied_kernel_count + i) * 4,
                )
                db_sess.add(kernel)

        # Create a copy of test_case with the actual random agent_id
        test_case_with_random_id = copy(test_case)
        test_case_with_random_id.agent_id = actual_agent_id

        yield test_case_with_random_id

    @pytest.fixture
    async def db_source(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[AgentDBSource, None]:
        """Create AgentDBSource for testing"""
        db_source = AgentDBSource(db=db_with_tables)
        yield db_source

    @pytest.mark.parametrize(
        "agent_with_kernels",
        [
            KernelFilteringTestCase(
                test_id="mixed_kernels",
                agent_id=AgentId(f"agent-mixed-{uuid4().hex[:8]}"),
                occupied_kernel_count=3,
                non_occupied_kernel_count=2,
                cpu_per_kernel=Decimal("1.0"),
                expected_actual_occupied_cpu=Decimal("3.0"),
            ),
            KernelFilteringTestCase(
                test_id="only_occupied",
                agent_id=AgentId(f"agent-only-occupied-{uuid4().hex[:8]}"),
                occupied_kernel_count=4,
                non_occupied_kernel_count=0,
                cpu_per_kernel=Decimal("2.0"),
                expected_actual_occupied_cpu=Decimal("8.0"),
            ),
            KernelFilteringTestCase(
                test_id="only_non_occupied",
                agent_id=AgentId(f"agent-only-non-occupied-{uuid4().hex[:8]}"),
                occupied_kernel_count=0,
                non_occupied_kernel_count=5,
                cpu_per_kernel=Decimal("1.0"),
                expected_actual_occupied_cpu=Decimal("0.0"),
            ),
            KernelFilteringTestCase(
                test_id="no_kernels",
                agent_id=AgentId(f"agent-no-kernels-{uuid4().hex[:8]}"),
                occupied_kernel_count=0,
                non_occupied_kernel_count=0,
                cpu_per_kernel=Decimal("0.0"),
                expected_actual_occupied_cpu=Decimal("0.0"),
            ),
        ],
        indirect=True,
        ids=["mixed_kernels", "only_occupied", "only_non_occupied", "no_kernels"],
    )
    async def test_search_agents_validates_actual_occupied_slots(
        self,
        db_source: AgentDBSource,
        agent_with_kernels: KernelFilteringTestCase,
    ) -> None:
        """Test that actual_occupied_slots correctly reflects kernel filtering via with_loader_criteria"""
        # Filter to only this test case's agent
        querier = BatchQuerier(
            pagination=OffsetPagination(offset=0, limit=10),
            conditions=[lambda: AgentRow.id == agent_with_kernels.agent_id],
        )

        result = await db_source.search_agents(querier)

        assert len(result.items) == 1
        agent_detail = result.items[0]

        # Validate actual_occupied_slots reflects only resource-occupied kernels
        actual_cpu = agent_detail.agent.actual_occupied_slots.get("cpu", 0)
        assert Decimal(str(actual_cpu)) == agent_with_kernels.expected_actual_occupied_cpu
