"""
Tests for ScheduleRepository functionality.
Tests the repository layer with real database operations using fixtures.
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from dateutil.tz import tzutc

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    AgentSelectionStrategy,
    ResourceSlot,
    SessionId,
    SessionTypes,
)
from ai.backend.manager.config.loader.legacy_etcd_loader import LegacyEtcdLoader
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models import (
    AgentRow,
    AgentStatus,
    DomainRow,
    GroupRow,
    KernelRow,
    KernelStatus,
    KeyPairResourcePolicyRow,
    KeyPairRow,
    ScalingGroupOpts,
    ScalingGroupRow,
    SessionDependencyRow,
    SessionRow,
    SessionStatus,
    UserRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.schedule.repository import ScheduleRepository
from ai.backend.manager.sokovan.scheduler.scheduler import SchedulingConfig
from ai.backend.manager.sokovan.scheduler.selectors.selector import AgentInfo
from ai.backend.manager.sokovan.scheduler.types import SystemSnapshot


@pytest.fixture
async def sample_scaling_groups(
    database_engine: ExtendedAsyncSAEngine,
) -> AsyncGenerator[list[ScalingGroupRow], None]:
    """Create sample scaling groups for testing"""
    scaling_groups = []
    async with database_engine.begin_session() as db_sess:
        for i in range(2):
            sg = ScalingGroupRow(
                name=f"test-sgroup-{i}",
                driver="test-driver",
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(
                    allowed_session_types=[SessionTypes.INTERACTIVE, SessionTypes.BATCH],
                    pending_timeout=timedelta(seconds=300),
                    agent_selection_strategy=AgentSelectionStrategy.ROUNDROBIN,
                    enforce_spreading_endpoint_replica=i == 1,  # True for second group
                ),
                driver_opts={},
                use_host_network=False,
                wsproxy_addr=None,
                wsproxy_api_token=None,
                is_active=True,
            )
            db_sess.add(sg)
            scaling_groups.append(sg)
        await db_sess.commit()

    yield scaling_groups

    # Cleanup
    async with database_engine.begin_session() as db_sess:
        for sg in scaling_groups:
            await db_sess.delete(sg)
        await db_sess.commit()


@pytest.fixture
async def sample_agents(
    database_engine: ExtendedAsyncSAEngine,
    sample_scaling_groups: list[ScalingGroupRow],
) -> AsyncGenerator[list[AgentRow], None]:
    """Create sample agents for testing"""
    agents = []
    async with database_engine.begin_session() as db_sess:
        # Create agents for first scaling group
        for i in range(3):
            agent = AgentRow(
                id=AgentId(f"agent-{i}"),
                status=AgentStatus.ALIVE if i < 2 else AgentStatus.LOST,
                status_changed=datetime.now(tzutc()),
                region="test-region",
                scaling_group=sample_scaling_groups[0].name,
                schedulable=i != 1,  # Second agent is not schedulable
                available_slots=ResourceSlot({"cpu": Decimal("8.0"), "mem": Decimal("16384")}),
                occupied_slots=ResourceSlot({"cpu": Decimal("2.0"), "mem": Decimal("4096")}),
                addr=f"10.0.0.{i + 1}:2001",
                architecture="x86_64",
                version="24.03.0",
            )
            db_sess.add(agent)
            agents.append(agent)

        # Create agent for second scaling group
        agent = AgentRow(
            id=AgentId("agent-3"),
            status=AgentStatus.ALIVE,
            status_changed=datetime.now(tzutc()),
            region="test-region",
            scaling_group=sample_scaling_groups[1].name,
            schedulable=True,
            available_slots=ResourceSlot({"cpu": Decimal("16.0"), "mem": Decimal("32768")}),
            occupied_slots=ResourceSlot({"cpu": Decimal("0.0"), "mem": Decimal("0")}),
            addr="10.0.0.4:2001",
            architecture="aarch64",
            version="24.03.0",
        )
        db_sess.add(agent)
        agents.append(agent)

        await db_sess.commit()

    yield agents

    # Cleanup
    async with database_engine.begin_session() as db_sess:
        for agent in agents:
            await db_sess.delete(agent)
        await db_sess.commit()


@pytest.fixture
async def sample_resource_policies(
    database_engine: ExtendedAsyncSAEngine,
) -> AsyncGenerator[dict[str, Any], None]:
    """Create sample resource policies for testing"""
    async with database_engine.begin_session() as db_sess:
        # Create keypair resource policy
        kp_policy = KeyPairResourcePolicyRow(
            name="test-keypair-policy",
            total_resource_slots=ResourceSlot({"cpu": Decimal("100"), "mem": Decimal("102400")}),
            max_concurrent_sessions=10,
            max_concurrent_sftp_sessions=2,
            max_pending_session_count=5,
            max_pending_session_resource_slots=ResourceSlot({
                "cpu": Decimal("50"),
                "mem": Decimal("51200"),
            }),
            max_containers_per_session=10,
            idle_timeout=3600,
        )
        db_sess.add(kp_policy)

        await db_sess.commit()

    yield {"keypair_policy": kp_policy}

    # Cleanup
    async with database_engine.begin_session() as db_sess:
        await db_sess.delete(kp_policy)
        await db_sess.commit()


@pytest.fixture
async def sample_sessions_and_kernels(
    database_engine: ExtendedAsyncSAEngine,
    sample_scaling_groups: list[ScalingGroupRow],
    sample_agents: list[AgentRow],
    sample_resource_policies: dict[str, Any],
) -> AsyncGenerator[dict[str, Any], None]:
    """Create sample sessions and kernels for testing"""
    data: dict[str, Any] = {
        "domains": [],
        "groups": [],
        "users": [],
        "keypairs": [],
        "sessions": [],
        "kernels": [],
        "dependencies": [],
    }

    async with database_engine.begin_session() as db_sess:
        # Create domain
        domain = DomainRow(
            name="test-domain",
            total_resource_slots=ResourceSlot({"cpu": Decimal("1000"), "mem": Decimal("1048576")}),
        )
        db_sess.add(domain)
        data["domains"].append(domain)

        # Create group
        group = GroupRow(
            id=uuid.uuid4(),
            name="test-group",
            domain_name=domain.name,
            total_resource_slots=ResourceSlot({"cpu": Decimal("500"), "mem": Decimal("524288")}),
        )
        db_sess.add(group)
        data["groups"].append(group)

        # Create user
        user = UserRow(
            uuid=uuid.uuid4(),
            username="testuser",
            email="test@example.com",
            password="dummy",
            domain_name=domain.name,
            role="user",
        )
        db_sess.add(user)
        data["users"].append(user)

        # Create keypair
        keypair = KeyPairRow(
            access_key=AccessKey("test-access-key"),
            secret_key="dummy-secret",
            user_id=user.email,
            user=user.uuid,
            is_active=True,
            resource_policy=sample_resource_policies["keypair_policy"].name,
        )
        db_sess.add(keypair)
        data["keypairs"].append(keypair)

        # Create sessions with different statuses
        for i, status in enumerate([
            SessionStatus.PENDING,
            SessionStatus.PENDING,
            SessionStatus.RUNNING,
        ]):
            session = SessionRow(
                id=SessionId(uuid.uuid4()),
                name=f"test-session-{i}",
                session_type=SessionTypes.INTERACTIVE,
                domain_name=domain.name,
                group_id=group.id,
                user_uuid=user.uuid,
                access_key=keypair.access_key,
                scaling_group_name=sample_scaling_groups[0].name,
                status=status,
                requested_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4096")}),
                created_at=datetime.now(tzutc()) - timedelta(minutes=i * 10),
            )
            db_sess.add(session)
            data["sessions"].append(session)

            # Create kernel for each session
            kernel = KernelRow(
                id=uuid.uuid4(),
                session_id=session.id,
                access_key=keypair.access_key,
                agent=sample_agents[0].id if status == SessionStatus.RUNNING else None,
                agent_addr=sample_agents[0].addr if status == SessionStatus.RUNNING else None,
                scaling_group=sample_scaling_groups[0].name,
                cluster_idx=0,
                cluster_role="main",
                cluster_hostname=f"kernel-{i}",
                image="python:3.8",
                architecture="x86_64",
                registry="docker.io",
                status=KernelStatus.PENDING
                if status == SessionStatus.PENDING
                else KernelStatus.RUNNING,
                status_changed=datetime.now(tzutc()),
                occupied_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4096")}),
                requested_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4096")}),
                domain_name=domain.name,
                group_id=group.id,
                user_uuid=user.uuid,
            )
            db_sess.add(kernel)
            data["kernels"].append(kernel)

        # Create session dependencies
        dep = SessionDependencyRow(
            session_id=data["sessions"][1].id,
            depends_on=data["sessions"][0].id,
        )
        db_sess.add(dep)
        data["dependencies"].append(dep)

        await db_sess.commit()

    yield data

    # Cleanup
    async with database_engine.begin_session() as db_sess:
        # Delete in reverse order of dependencies
        for dep in data["dependencies"]:
            await db_sess.delete(dep)
        for kernel in data["kernels"]:
            await db_sess.delete(kernel)
        for session in data["sessions"]:
            await db_sess.delete(session)
        for keypair in data["keypairs"]:
            await db_sess.delete(keypair)
        for user in data["users"]:
            await db_sess.delete(user)
        for group in data["groups"]:
            await db_sess.delete(group)
        for domain in data["domains"]:
            await db_sess.delete(domain)
        await db_sess.commit()


@pytest.fixture
def mock_valkey_stat_client() -> ValkeyStatClient:
    """Create mock Valkey stat client"""
    mock_client = MagicMock(spec=ValkeyStatClient)
    mock_client.get_keypair_concurrency_used = AsyncMock(return_value=2)
    mock_client._get_raw = AsyncMock(return_value=b"1")
    return mock_client


@pytest.fixture
def mock_config_provider() -> ManagerConfigProvider:
    """Create mock config provider"""
    mock_provider = MagicMock(spec=ManagerConfigProvider)
    mock_legacy_loader = MagicMock(spec=LegacyEtcdLoader)
    mock_legacy_loader.get_resource_slots = AsyncMock(return_value={"cpu": "count", "mem": "bytes"})
    mock_legacy_loader.get_raw = AsyncMock(return_value="10")  # max_container_count
    mock_provider.legacy_etcd_config_loader = mock_legacy_loader
    return mock_provider


@pytest.fixture
async def schedule_repository(
    database_engine: ExtendedAsyncSAEngine,
    mock_valkey_stat_client: ValkeyStatClient,
    mock_config_provider: ManagerConfigProvider,
) -> ScheduleRepository:
    """Create ScheduleRepository instance"""
    return ScheduleRepository(
        db=database_engine,
        valkey_stat=mock_valkey_stat_client,
        config_provider=mock_config_provider,
    )


class TestScheduleRepository:
    """Test cases for ScheduleRepository"""

    async def test_get_agents_with_single_scaling_group(
        self,
        schedule_repository: ScheduleRepository,
        sample_scaling_groups: list[ScalingGroupRow],
        sample_agents: list[AgentRow],
    ):
        """Test getting agents from a single scaling group"""
        agents = await schedule_repository.get_agents(sample_scaling_groups[0].name)

        # Should return only alive, schedulable agents from the first scaling group
        assert len(agents) == 1
        assert agents[0].agent_id == AgentId("agent-0")
        assert agents[0].scaling_group == sample_scaling_groups[0].name
        assert agents[0].architecture == "x86_64"
        assert agents[0].available_slots["cpu"] == Decimal("8.0")
        assert agents[0].occupied_slots["cpu"] == Decimal("2.0")
        assert agents[0].container_count == 0

    async def test_get_agents_empty_scaling_group(
        self,
        schedule_repository: ScheduleRepository,
    ):
        """Test getting agents from non-existent scaling group"""
        agents = await schedule_repository.get_agents("non-existent-sgroup")
        assert len(agents) == 0

    async def test_get_agents_returns_correct_agent_info(
        self,
        schedule_repository: ScheduleRepository,
        sample_scaling_groups: list[ScalingGroupRow],
        sample_agents: list[AgentRow],
    ):
        """Test that AgentInfo objects have correct fields"""
        agents = await schedule_repository.get_agents(sample_scaling_groups[1].name)

        assert len(agents) == 1
        agent_info = agents[0]

        # Verify all AgentInfo fields
        assert isinstance(agent_info, AgentInfo)
        assert agent_info.agent_id == AgentId("agent-3")
        assert agent_info.agent_addr == "10.0.0.4:2001"
        assert agent_info.architecture == "aarch64"
        assert agent_info.available_slots == ResourceSlot({
            "cpu": Decimal("16.0"),
            "mem": Decimal("32768"),
        })
        assert agent_info.occupied_slots == ResourceSlot({
            "cpu": Decimal("0.0"),
            "mem": Decimal("0"),
        })
        assert agent_info.scaling_group == sample_scaling_groups[1].name
        assert agent_info.container_count == 0

    async def test_get_system_snapshot_complete_data(
        self,
        schedule_repository: ScheduleRepository,
        sample_scaling_groups: list[ScalingGroupRow],
        sample_agents: list[AgentRow],
        sample_sessions_and_kernels: dict[str, Any],
    ):
        """Test getting complete system snapshot"""
        snapshot = await schedule_repository.get_system_snapshot(sample_scaling_groups[0].name)

        assert isinstance(snapshot, SystemSnapshot)

        # Check total capacity (from the one alive, schedulable agent)
        assert snapshot.total_capacity["cpu"] == Decimal("8.0")
        assert snapshot.total_capacity["mem"] == Decimal("16384")

        # Check resource occupancy
        assert AccessKey("test-access-key") in snapshot.resource_occupancy.by_keypair
        assert snapshot.resource_occupancy.by_keypair[AccessKey("test-access-key")][
            "cpu"
        ] == Decimal("2")

        # Check resource policy
        assert AccessKey("test-access-key") in snapshot.resource_policy.keypair_policies
        policy = snapshot.resource_policy.keypair_policies[AccessKey("test-access-key")]
        assert policy.max_concurrent_sessions == 10

        # Check concurrency
        assert snapshot.concurrency.sessions_by_keypair[AccessKey("test-access-key")] == 2
        assert snapshot.concurrency.sftp_sessions_by_keypair[AccessKey("test-access-key")] == 1

        # Check pending sessions
        assert AccessKey("test-access-key") in snapshot.pending_sessions.by_keypair
        assert len(snapshot.pending_sessions.by_keypair[AccessKey("test-access-key")]) == 2

        # Check session dependencies
        # We need to check using the actual session IDs from the fixture
        session_with_deps = None
        for session_id, deps in snapshot.session_dependencies.by_session.items():
            if len(deps) > 0:
                session_with_deps = session_id
                assert len(deps) == 1
                # Verify the dependency exists
                break
        assert session_with_deps is not None

    async def test_get_system_snapshot_filters_by_scaling_group(
        self,
        schedule_repository: ScheduleRepository,
        sample_scaling_groups: list[ScalingGroupRow],
        sample_agents: list[AgentRow],
    ):
        """Test that system snapshot is filtered by scaling group"""
        # Get snapshot for first scaling group
        snapshot1 = await schedule_repository.get_system_snapshot(sample_scaling_groups[0].name)
        assert snapshot1.total_capacity["cpu"] == Decimal("8.0")  # From agent-0

        # Get snapshot for second scaling group
        snapshot2 = await schedule_repository.get_system_snapshot(sample_scaling_groups[1].name)
        assert snapshot2.total_capacity["cpu"] == Decimal("16.0")  # From agent-3

    async def test_get_system_snapshot_empty_scaling_group(
        self,
        schedule_repository: ScheduleRepository,
    ):
        """Test system snapshot for non-existent scaling group"""
        snapshot = await schedule_repository.get_system_snapshot("non-existent-sgroup")

        assert snapshot.total_capacity == ResourceSlot()
        assert len(snapshot.resource_occupancy.by_keypair) == 0
        assert len(snapshot.resource_policy.keypair_policies) == 0
        assert len(snapshot.concurrency.sessions_by_keypair) == 0
        assert len(snapshot.pending_sessions.by_keypair) == 0
        assert len(snapshot.session_dependencies.by_session) == 0

    async def test_get_scheduling_config_with_defaults(
        self,
        schedule_repository: ScheduleRepository,
        sample_scaling_groups: list[ScalingGroupRow],
    ):
        """Test getting scheduling config with default values"""
        config = await schedule_repository.get_scheduling_config(sample_scaling_groups[0].name)

        assert isinstance(config, SchedulingConfig)
        assert config.max_container_count_per_agent == 10  # From mock etcd
        assert config.enforce_spreading_endpoint_replica is False  # From sgroup opts

    async def test_get_scheduling_config_with_enforce_spreading(
        self,
        schedule_repository: ScheduleRepository,
        sample_scaling_groups: list[ScalingGroupRow],
    ):
        """Test scheduling config with enforce_spreading enabled"""
        config = await schedule_repository.get_scheduling_config(sample_scaling_groups[1].name)

        assert config.max_container_count_per_agent == 10
        assert config.enforce_spreading_endpoint_replica is True  # From sgroup opts

    async def test_get_scheduling_config_no_etcd_value(
        self,
        schedule_repository: ScheduleRepository,
        sample_scaling_groups: list[ScalingGroupRow],
        mock_config_provider: ManagerConfigProvider,
    ):
        """Test scheduling config when etcd has no value"""
        # Mock etcd returning None
        mock_config_provider.legacy_etcd_config_loader.get_raw = AsyncMock(return_value=None)  # type: ignore[method-assign]

        config = await schedule_repository.get_scheduling_config(sample_scaling_groups[0].name)

        assert config.max_container_count_per_agent is None
        assert config.enforce_spreading_endpoint_replica is False

    async def test_get_scheduling_config_invalid_scaling_group(
        self,
        schedule_repository: ScheduleRepository,
    ):
        """Test scheduling config with invalid scaling group"""
        with pytest.raises(ValueError, match="Scaling group.*not found"):
            await schedule_repository.get_scheduling_config("non-existent-sgroup")

    async def test_repository_methods_integration(
        self,
        schedule_repository: ScheduleRepository,
        sample_scaling_groups: list[ScalingGroupRow],
        sample_agents: list[AgentRow],
        sample_sessions_and_kernels: dict[str, Any],
    ):
        """Test using all three methods together"""
        scaling_group = sample_scaling_groups[0].name

        # Get agents
        agents = await schedule_repository.get_agents(scaling_group)
        assert len(agents) > 0

        # Get system snapshot
        snapshot = await schedule_repository.get_system_snapshot(scaling_group)
        assert snapshot.total_capacity["cpu"] > 0

        # Get scheduling config
        config = await schedule_repository.get_scheduling_config(scaling_group)
        assert config.max_container_count_per_agent is not None

        # Verify consistency between methods
        # Total capacity should match sum of available slots from agents
        total_cpu = sum(agent.available_slots.get("cpu", 0) for agent in agents)
        assert snapshot.total_capacity["cpu"] == total_cpu
