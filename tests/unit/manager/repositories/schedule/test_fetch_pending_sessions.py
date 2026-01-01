"""
Test for _fetch_pending_sessions_join method specifically.
Separated to debug SQLAlchemy property object error.
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.types import (
    AccessKey,
    AgentSelectionStrategy,
    ClusterMode,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.config.loader.legacy_etcd_loader import LegacyEtcdLoader
from ai.backend.manager.config.provider import ManagerConfigProvider
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
        ],
    ):
        yield database_connection


@pytest.fixture
async def minimal_setup(
    db_with_cleanup: ExtendedAsyncSAEngine,
) -> AsyncGenerator[dict[str, Any], None]:
    """Create minimal setup for testing _fetch_pending_sessions_join"""
    data: dict[str, Any] = {}

    async with db_with_cleanup.begin_session() as db_sess:
        # Create scaling group
        sg = ScalingGroupRow(
            name="test-sgroup",
            driver="test-driver",
            scheduler="fifo",
            scheduler_opts=ScalingGroupOpts(
                allowed_session_types=[SessionTypes.INTERACTIVE, SessionTypes.BATCH],
                pending_timeout=timedelta(seconds=300),
                agent_selection_strategy=AgentSelectionStrategy.ROUNDROBIN,
            ),
            driver_opts={},
            use_host_network=False,
            is_active=True,
        )
        db_sess.add(sg)
        data["scaling_group"] = sg

        # Create domain
        domain = DomainRow(
            name="test-domain",
            total_resource_slots=ResourceSlot({"cpu": Decimal("1000"), "mem": Decimal("1048576")}),
        )
        db_sess.add(domain)
        data["domain"] = domain

        # Create policies
        user_policy = UserResourcePolicyRow(
            name="test-policy",
            max_vfolder_count=10,
            max_quota_scope_size=-1,
            max_session_count_per_model_session=10,
            max_customized_image_count=10,
        )
        db_sess.add(user_policy)

        project_policy = ProjectResourcePolicyRow(
            name="test-policy",
            max_vfolder_count=10,
            max_quota_scope_size=-1,
            max_network_count=10,
        )
        db_sess.add(project_policy)

        kp_policy = KeyPairResourcePolicyRow(
            name="test-policy",
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

        # Create group
        group = GroupRow(
            id=uuid.uuid4(),
            name="test-group",
            domain_name=domain.name,
            total_resource_slots=ResourceSlot({"cpu": Decimal("500"), "mem": Decimal("524288")}),
            resource_policy="test-policy",
        )
        db_sess.add(group)
        data["group"] = group

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
            resource_policy="test-policy",
        )
        db_sess.add(user)
        data["user"] = user

        await db_sess.commit()

        # Create keypair
        keypair = KeyPairRow(
            access_key=AccessKey("test-access-key"),
            secret_key="dummy-secret",
            user_id=user.email,
            user=user.uuid,
            is_active=True,
            resource_policy="test-policy",
        )
        db_sess.add(keypair)
        data["keypair"] = keypair

        # Create pending session
        session = SessionRow(
            id=SessionId(uuid.uuid4()),
            name="test-session",
            session_type=SessionTypes.INTERACTIVE,
            domain_name=domain.name,
            group_id=group.id,
            user_uuid=user.uuid,
            access_key=keypair.access_key,
            scaling_group_name=sg.name,
            status=SessionStatus.PENDING,
            cluster_mode=ClusterMode.SINGLE_NODE,
            requested_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4096")}),
            created_at=datetime.now(tzutc()),
            images=["python:3.8"],
            vfolder_mounts=[],
            environ={},
            result=SessionResult.UNDEFINED,
        )
        db_sess.add(session)
        data["session"] = session

        # Create kernel for the session
        kernel = KernelRow(
            id=uuid.uuid4(),
            session_id=session.id,
            access_key=keypair.access_key,
            agent=None,  # Pending kernel has no agent
            agent_addr=None,
            scaling_group=sg.name,
            cluster_idx=0,
            cluster_role="main",
            cluster_hostname="kernel-0",
            image="python:3.8",
            architecture="x86_64",
            registry="docker.io",
            status=KernelStatus.PENDING,
            status_changed=datetime.now(tzutc()),
            occupied_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4096")}),
            requested_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4096")}),
            domain_name=domain.name,
            group_id=group.id,
            user_uuid=user.uuid,
            mounts=[],
            environ={},
            vfolder_mounts=[],
            preopen_ports=[],
            repl_in_port=2001,
            repl_out_port=2002,
            stdin_port=2003,
            stdout_port=2004,
        )
        db_sess.add(kernel)
        data["kernel"] = kernel

        await db_sess.commit()

    yield data


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
    mock_legacy_loader.get_raw = AsyncMock(return_value="10")
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


class TestFetchPendingSessions:
    """Test _fetch_pending_sessions_join method specifically"""

    async def test_fetch_pending_sessions_join_basic(
        self,
        schedule_repository: ScheduleRepository,
        minimal_setup: dict[str, Any],
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Test basic functionality of _fetch_pending_sessions_join"""
        scaling_group = minimal_setup["scaling_group"].name

        # Call the method directly
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            result = await schedule_repository._fetch_pending_sessions_join(db_sess, scaling_group)

        # Verify results
        assert len(result) == 1
        session_data = result[0]

        # Check session data
        assert session_data.id == minimal_setup["session"].id
        assert session_data.access_key == minimal_setup["session"].access_key
        assert session_data.scaling_group_name == scaling_group

        # Check kernel data
        assert len(session_data.kernels) == 1
        kernel_data = session_data.kernels[0]
        assert kernel_data.id == minimal_setup["kernel"].id
        assert kernel_data.image == "python:3.8"
        assert kernel_data.architecture == "x86_64"
        assert kernel_data.agent is None  # Pending kernel has no agent

    async def test_fetch_pending_sessions_join_with_old_session(
        self,
        schedule_repository: ScheduleRepository,
        minimal_setup: dict[str, Any],
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Test that old sessions are still fetched (no timeout filtering)"""
        scaling_group = minimal_setup["scaling_group"].name
        session_id = minimal_setup["session"].id

        # First, update the session to be older
        async with db_with_cleanup.begin_session() as db_sess:
            # Query the session from DB to get it attached to this session
            stmt = (
                sa.update(SessionRow)
                .where(SessionRow.id == session_id)
                .values(created_at=datetime.now(tzutc()) - timedelta(minutes=10))
            )
            await db_sess.execute(stmt)
            await db_sess.commit()

        # Call the method
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            result = await schedule_repository._fetch_pending_sessions_join(db_sess, scaling_group)

        # Should still return the session as there's no timeout filtering
        assert len(result) == 1
        assert result[0].id == session_id

    async def test_fetch_pending_sessions_join_no_sessions(
        self,
        schedule_repository: ScheduleRepository,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Test with non-existent scaling group"""
        scaling_group = "non-existent-sgroup"

        # Call the method
        async with db_with_cleanup.begin_readonly_session() as db_sess:
            result = await schedule_repository._fetch_pending_sessions_join(db_sess, scaling_group)

        # Should return empty list
        assert len(result) == 0
        assert result == []
