"""Regression tests: cancellation paths must set ``resource_allocations.free_at``
in the same transaction. Covers ``_cancel_pending_sessions`` (via
``mark_sessions_terminating``) and ``cancel_kernels_for_failed_image``.
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    ClusterMode,
    DefaultForUnspecified,
    KernelId,
    ResourceSlot,
    SecretKey,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import (
    AssociationScopesEntitiesRow,
    EntityFieldRow,
    RoleRow,
    UserRoleRow,
)
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_slot import AgentResourceRow, ResourceAllocationRow
from ai.backend.manager.models.resource_slot.row import ResourceSlotTypeRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.scheduling_history.row import SessionSchedulingHistoryRow
from ai.backend.manager.models.session import SessionDependencyRow, SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource
from ai.backend.testutils.db import with_tables

_BASE_TABLES = [
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
    AssociationScopesEntitiesRow,
    EntityFieldRow,
    AgentRow,
    SessionRow,
    KernelRow,
    ResourceSlotTypeRow,
    ResourceAllocationRow,
    AgentResourceRow,
    SessionDependencyRow,
    SessionSchedulingHistoryRow,
]


class TestCancelFreesResourceAllocations:
    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(database_connection, _BASE_TABLES):
            yield database_connection

    @pytest.fixture
    async def test_domain_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    name=domain_name,
                    total_resource_slots=ResourceSlot({
                        "cpu": Decimal("1000"),
                        "mem": Decimal("1048576"),
                    }),
                )
            )
            await db_sess.flush()
        yield domain_name

    @pytest.fixture
    async def test_scaling_group_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        sg_name = f"test-sgroup-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                ScalingGroupRow(
                    name=sg_name,
                    driver="static",
                    scheduler="fifo",
                    scheduler_opts=ScalingGroupOpts(
                        allowed_session_types=[],
                        pending_timeout=timedelta(hours=1),
                        config={},
                    ),
                    driver_opts={},
                    is_active=True,
                )
            )
            await db_sess.flush()
        yield sg_name

    @pytest.fixture
    async def test_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_network_count=10,
                )
            )
            await db_sess.flush()
        yield policy_name

    @pytest.fixture
    async def test_user_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        policy_name = f"test-user-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                UserResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=3,
                )
            )
            await db_sess.flush()
        yield policy_name

    @pytest.fixture
    async def test_keypair_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        policy_name = f"test-keypair-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                KeyPairResourcePolicyRow(
                    name=policy_name,
                    default_for_unspecified=DefaultForUnspecified.LIMITED,
                    total_resource_slots=ResourceSlot({
                        "cpu": Decimal("100"),
                        "mem": Decimal("102400"),
                    }),
                    max_concurrent_sessions=10,
                    max_containers_per_session=1,
                    idle_timeout=600,
                    max_session_lifetime=0,
                    allowed_vfolder_hosts={},
                )
            )
            await db_sess.flush()
        yield policy_name

    @pytest.fixture
    async def test_user_uuid(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_user_resource_policy_name: str,
    ) -> AsyncGenerator[uuid.UUID, None]:
        user_uuid = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                UserRow(
                    uuid=user_uuid,
                    email=f"test-user-{uuid.uuid4().hex[:8]}@test.com",
                    username=f"test-user-{uuid.uuid4().hex[:8]}",
                    role=UserRole.USER,
                    status=UserStatus.ACTIVE,
                    domain_name=test_domain_name,
                    resource_policy=test_user_resource_policy_name,
                )
            )
            await db_sess.flush()
        yield user_uuid

    @pytest.fixture
    async def test_access_key(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_user_uuid: uuid.UUID,
        test_keypair_resource_policy_name: str,
    ) -> AsyncGenerator[AccessKey, None]:
        access_key = AccessKey(f"AKIA{uuid.uuid4().hex[:16].upper()}")
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                KeyPairRow(
                    user_id=f"test-user-{uuid.uuid4().hex[:8]}@test.com",
                    access_key=access_key,
                    secret_key=SecretKey(f"SK{uuid.uuid4().hex}"),
                    is_active=True,
                    is_admin=False,
                    resource_policy=test_keypair_resource_policy_name,
                    rate_limit=1000,
                    num_queries=0,
                    user=test_user_uuid,
                )
            )
            await db_sess.flush()
        yield access_key

    @pytest.fixture
    async def test_group_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_resource_policy_name: str,
    ) -> AsyncGenerator[uuid.UUID, None]:
        group_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                GroupRow(
                    id=group_id,
                    name=f"test-group-{uuid.uuid4().hex[:8]}",
                    description="Test group",
                    is_active=True,
                    domain_name=test_domain_name,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    resource_policy=test_resource_policy_name,
                )
            )
            await db_sess.flush()
        yield group_id

    @pytest.fixture
    async def test_agent_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_scaling_group_name: str,
    ) -> AsyncGenerator[str, None]:
        agent_id = f"test-agent-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                AgentRow(
                    id=agent_id,
                    status=AgentStatus.ALIVE,
                    region="local",
                    scaling_group=test_scaling_group_name,
                    available_slots=ResourceSlot({"cpu": Decimal("10"), "mem": Decimal("10240")}),
                    occupied_slots=ResourceSlot(),
                    addr="127.0.0.1:6001",
                    version="1.0.0",
                    architecture="x86_64",
                )
            )
            await db_sess.flush()
        yield agent_id

    @pytest.fixture
    async def resource_slot_types(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[None, None]:
        async with db_with_cleanup.begin_session() as db_sess:
            for slot_name, slot_type in [("cpu", "count"), ("mem", "bytes")]:
                db_sess.add(ResourceSlotTypeRow(slot_name=slot_name, slot_type=slot_type))
            await db_sess.flush()
        yield

    async def _insert_session(
        self,
        db: ExtendedAsyncSAEngine,
        *,
        kernel_status: KernelStatus,
        domain_name: str,
        scaling_group_name: str,
        group_id: uuid.UUID,
        user_uuid: uuid.UUID,
        access_key: AccessKey,
        agent_id: str | None,
        image: str = "python:3.8",
    ) -> tuple[SessionId, KernelId]:
        session_id = SessionId(uuid.uuid4())
        kernel_id = KernelId(uuid.uuid4())
        cpu = Decimal("2")
        mem = Decimal("4096")
        session_status = (
            SessionStatus.PENDING
            if kernel_status == KernelStatus.PENDING
            else SessionStatus.PREPARING
        )

        async with db.begin_session() as db_sess:
            db_sess.add(
                SessionRow(
                    id=session_id,
                    name=f"test-session-{uuid.uuid4().hex[:8]}",
                    session_type=SessionTypes.INTERACTIVE,
                    domain_name=domain_name,
                    group_id=group_id,
                    scaling_group_name=scaling_group_name,
                    status=session_status,
                    status_info="test",
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    requested_slots=ResourceSlot({"cpu": cpu, "mem": mem}),
                    created_at=datetime.now(tzutc()),
                    images=[image],
                    vfolder_mounts=[],
                    environ={},
                    result=SessionResult.UNDEFINED,
                )
            )
            await db_sess.flush()

            db_sess.add(
                KernelRow(
                    id=kernel_id,
                    session_id=session_id,
                    agent=agent_id,
                    agent_addr="127.0.0.1:6001" if agent_id else None,
                    scaling_group=scaling_group_name,
                    cluster_idx=0,
                    cluster_role="main",
                    cluster_hostname=f"kernel-{uuid.uuid4().hex[:8]}",
                    image=image,
                    architecture="x86_64",
                    registry="docker.io",
                    container_id=None,
                    status=kernel_status,
                    status_changed=datetime.now(tzutc()),
                    occupied_slots=ResourceSlot(),
                    requested_slots=ResourceSlot({"cpu": cpu, "mem": mem}),
                    domain_name=domain_name,
                    group_id=group_id,
                    user_uuid=user_uuid,
                    access_key=access_key,
                    mounts=[],
                    environ={},
                    vfolder_mounts=[],
                    preopen_ports=[],
                    repl_in_port=2001,
                    repl_out_port=2002,
                    stdin_port=2003,
                    stdout_port=2004,
                )
            )
            await db_sess.flush()

            db_sess.add(
                ResourceAllocationRow(
                    kernel_id=kernel_id, slot_name="cpu", requested=cpu, used=None
                )
            )
            db_sess.add(
                ResourceAllocationRow(
                    kernel_id=kernel_id, slot_name="mem", requested=mem, used=None
                )
            )
            await db_sess.flush()

        return session_id, kernel_id

    @pytest.fixture
    async def pending_session(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        resource_slot_types: None,
    ) -> tuple[SessionId, KernelId]:
        return await self._insert_session(
            db_with_cleanup,
            kernel_status=KernelStatus.PENDING,
            domain_name=test_domain_name,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_id=None,
        )

    @pytest.fixture
    async def pulling_session_on_agent(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_scaling_group_name: str,
        test_group_id: uuid.UUID,
        test_user_uuid: uuid.UUID,
        test_access_key: AccessKey,
        test_agent_id: str,
        resource_slot_types: None,
    ) -> tuple[SessionId, KernelId, str]:
        session_id, kernel_id = await self._insert_session(
            db_with_cleanup,
            kernel_status=KernelStatus.PULLING,
            domain_name=test_domain_name,
            scaling_group_name=test_scaling_group_name,
            group_id=test_group_id,
            user_uuid=test_user_uuid,
            access_key=test_access_key,
            agent_id=test_agent_id,
            image="python:3.8",
        )
        return session_id, kernel_id, test_agent_id

    async def _assert_all_freed(self, db: ExtendedAsyncSAEngine, kernel_id: KernelId) -> None:
        async with db.begin_readonly_session() as db_sess:
            allocs = (
                (
                    await db_sess.execute(
                        sa.select(ResourceAllocationRow).where(
                            ResourceAllocationRow.kernel_id == kernel_id,
                        )
                    )
                )
                .scalars()
                .all()
            )
            assert len(allocs) == 2
            for alloc in allocs:
                assert alloc.free_at is not None, f"free_at must be set on slot {alloc.slot_name}"

    async def test_cancel_pending_sessions_sets_free_at(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        pending_session: tuple[SessionId, KernelId],
    ) -> None:
        session_id, kernel_id = pending_session
        db_source = ScheduleDBSource(db_with_cleanup)

        result = await db_source.mark_sessions_terminating([session_id])

        assert session_id in result.cancelled_sessions
        await self._assert_all_freed(db_with_cleanup, kernel_id)

    async def test_cancel_kernels_for_failed_image_sets_free_at(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        pulling_session_on_agent: tuple[SessionId, KernelId, str],
    ) -> None:
        session_id, kernel_id, agent_id = pulling_session_on_agent
        db_source = ScheduleDBSource(db_with_cleanup)

        affected = await db_source.cancel_kernels_for_failed_image(
            AgentId(agent_id), "python:3.8", "image pull failed for test"
        )

        assert session_id in affected
        await self._assert_all_freed(db_with_cleanup, kernel_id)
