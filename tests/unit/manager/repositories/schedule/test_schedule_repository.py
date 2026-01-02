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
    ClusterMode,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.config.loader.legacy_etcd_loader import LegacyEtcdLoader
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.data.user.types import UserRole
from ai.backend.manager.models import (
    AgentRow,
    DomainRow,
    GroupRow,
    KernelRow,
    KeyPairResourcePolicyRow,
    KeyPairRow,
    ProjectResourcePolicyRow,
    ScalingGroupOpts,
    ScalingGroupRow,
    SessionDependencyRow,
    SessionRow,
    UserResourcePolicyRow,
    UserRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.schedule.repository import ScheduleRepository
from ai.backend.testutils.db import with_tables


@pytest.fixture
async def db_with_cleanup(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    """Database connection with tables created. TRUNCATE CASCADE handles cleanup."""
    async with with_tables(
        database_connection,
        [
            ScalingGroupRow,
            DomainRow,
            UserResourcePolicyRow,
            ProjectResourcePolicyRow,
            KeyPairResourcePolicyRow,
            GroupRow,
            UserRow,
            KeyPairRow,
            AgentRow,
            SessionRow,
            KernelRow,
            SessionDependencyRow,
        ],
    ):
        yield database_connection


@pytest.fixture
async def sample_scaling_groups(
    db_with_cleanup: ExtendedAsyncSAEngine,
) -> AsyncGenerator[list[ScalingGroupRow], None]:
    """Create sample scaling groups for testing"""
    scaling_groups = []
    async with db_with_cleanup.begin_session() as db_sess:
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


@pytest.fixture
async def sample_agents(
    db_with_cleanup: ExtendedAsyncSAEngine,
    sample_scaling_groups: list[ScalingGroupRow],
) -> AsyncGenerator[list[AgentRow], None]:
    """Create sample agents for testing"""
    agents = []
    async with db_with_cleanup.begin_session() as db_sess:
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


@pytest.fixture
async def sample_resource_policies(
    db_with_cleanup: ExtendedAsyncSAEngine,
) -> AsyncGenerator[dict[str, Any], None]:
    """Create sample resource policies for testing"""
    async with db_with_cleanup.begin_session() as db_sess:
        # Create user resource policy first (for foreign key)
        user_policy = UserResourcePolicyRow(
            name="test-keypair-policy",  # Same name for simplicity
            max_vfolder_count=10,
            max_quota_scope_size=-1,
            max_session_count_per_model_session=10,
            max_customized_image_count=10,
        )
        db_sess.add(user_policy)

        # Create project resource policy (for foreign key)
        project_policy = ProjectResourcePolicyRow(
            name="test-keypair-policy",  # Same name to satisfy foreign key
            max_vfolder_count=10,
            max_quota_scope_size=-1,
            max_network_count=10,
        )
        db_sess.add(project_policy)

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

    yield {
        "keypair_policy": kp_policy,
        "project_policy": project_policy,
        "user_policy": user_policy,
    }


@pytest.fixture
async def sample_sessions_and_kernels(
    db_with_cleanup: ExtendedAsyncSAEngine,
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

    async with db_with_cleanup.begin_session() as db_sess:
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
            resource_policy=sample_resource_policies["keypair_policy"].name,  # Use the same policy
        )
        db_sess.add(group)
        data["groups"].append(group)

        # Create user
        from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
        from ai.backend.manager.models.hasher.types import PasswordInfo

        password_info = PasswordInfo(
            password="dummy",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=600_000,
            salt_size=32,
        )

        user = UserRow(
            uuid=uuid.uuid4(),
            username="testuser",
            email="test@example.com",
            password=password_info,
            domain_name=domain.name,
            role=UserRole.USER,
            resource_policy=sample_resource_policies["keypair_policy"].name,
        )
        db_sess.add(user)
        data["users"].append(user)

        # Commit users first to ensure foreign key constraint is satisfied
        await db_sess.commit()

        # Create keypair (needs user to exist due to foreign key)
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
                cluster_mode=ClusterMode.SINGLE_NODE,
                requested_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4096")}),
                created_at=datetime.now(tzutc()) - timedelta(minutes=i * 2),
                # Required fields
                images=["python:3.8"],
                vfolder_mounts=[],
                environ={},
                result=SessionResult.UNDEFINED,
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
                # Required fields for kernel
                mounts=[],
                environ={},
                vfolder_mounts=[],
                preopen_ports=[],
                # Port fields (required not null)
                repl_in_port=2001,
                repl_out_port=2002,
                stdin_port=2003,
                stdout_port=2004,
            )
            db_sess.add(kernel)
            data["kernels"].append(kernel)

        # Commit sessions and kernels first
        await db_sess.commit()

        # Create session dependencies after sessions are committed
        dep = SessionDependencyRow(
            session_id=data["sessions"][1].id,
            depends_on=data["sessions"][0].id,
        )
        db_sess.add(dep)
        data["dependencies"].append(dep)

        await db_sess.commit()

    yield data


@pytest.fixture
def mock_valkey_stat_client() -> ValkeyStatClient:
    """Create mock Valkey stat client"""
    mock_client = MagicMock(spec=ValkeyStatClient)
    mock_client.get_keypair_concurrency_used = AsyncMock(return_value=2)
    # Mock _get_multiple_keys to return appropriate values for concurrency tracking
    # Returns [sessions_count, sftp_sessions_count] for each access key
    mock_client._get_multiple_keys = AsyncMock(return_value=[b"2", b"1"])
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
    db_with_cleanup: ExtendedAsyncSAEngine,
    mock_valkey_stat_client: ValkeyStatClient,
    mock_config_provider: ManagerConfigProvider,
) -> ScheduleRepository:
    """Create ScheduleRepository instance"""
    return ScheduleRepository(
        db=db_with_cleanup,
        valkey_stat=mock_valkey_stat_client,
        config_provider=mock_config_provider,
    )


class TestScheduleRepository:
    """Test cases for ScheduleRepository"""
