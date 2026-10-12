"""
Tests for fetch_resource_usage and parse_resource_usage_groups against a real database.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.auth import PublicKey
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    DefaultForUnspecified,
    KernelId,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import ProjectRow, ProjectType
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.resource_group.types import ResourceGroupOpts
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_slot.row import ResourceAllocationRow, ResourceSlotTypeRow
from ai.backend.manager.models.resource_usage import (
    fetch_resource_usage,
    parse_resource_usage_groups,
    parse_total_resource_group,
)
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.user.row import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.secret.types import SecretValue
from ai.backend.testutils.db import with_tables

_DOMAIN = "usage-domain"
_PERIOD_START = datetime(2026, 9, 1, tzinfo=UTC)
_PERIOD_END = datetime(2026, 10, 1, tzinfo=UTC)
_LAST_STAT: dict[str, Any] = {"cpu_used": {"current": "10"}}
_AGENT_ID = "i-usage-agent"


@dataclass(frozen=True)
class _Owner:
    domain_id: DomainID
    resource_group_id: ResourceGroupID
    user_id: uuid.UUID
    access_key: AccessKey
    project_a: uuid.UUID
    project_b: uuid.UUID


class TestFetchResourceUsage:
    @pytest.fixture
    async def db(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ResourceGroupRow,
                AgentRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRow,
                ProjectRow,
                KeyPairRow,
                ContainerRegistryRow,
                ImageRow,
                SessionRow,
                KernelRow,
                ResourceSlotTypeRow,
                ResourceAllocationRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def owner(self, db: ExtendedAsyncSAEngine) -> _Owner:
        """A user with a keypair and two projects in one domain."""
        owner = _Owner(
            domain_id=DomainID(uuid.uuid4()),
            resource_group_id=ResourceGroupID(uuid.uuid4()),
            user_id=uuid.uuid4(),
            access_key=AccessKey("AKIAUSAGETEST0001"),
            project_a=uuid.uuid4(),
            project_b=uuid.uuid4(),
        )
        async with db.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    id=owner.domain_id,
                    name=_DOMAIN,
                    description="",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                    integration_id=None,
                )
            )
            db_sess.add(
                ResourceGroupRow(
                    id=owner.resource_group_id,
                    name="default",
                    is_active=True,
                    is_public=True,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    scheduler_opts=ResourceGroupOpts(),
                )
            )
            db_sess.add(
                UserResourcePolicyRow(
                    name="usage-user-policy",
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
            db_sess.add(
                ProjectResourcePolicyRow(
                    name="usage-project-policy",
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_network_count=10,
                )
            )
            db_sess.add(
                KeyPairResourcePolicyRow(
                    name="usage-keypair-policy",
                    default_for_unspecified=DefaultForUnspecified.UNLIMITED,
                    total_resource_slots=ResourceSlot(),
                    max_session_lifetime=0,
                    max_concurrent_sessions=10,
                    max_concurrent_sftp_sessions=5,
                    max_containers_per_session=1,
                    idle_timeout=3600,
                )
            )
            await db_sess.flush()
            db_sess.add(
                UserRow(
                    uuid=owner.user_id,
                    username="usage-user",
                    email="usage@example.com",
                    password=None,
                    need_password_change=False,
                    full_name="Usage User",
                    description="",
                    status=UserStatus.ACTIVE,
                    status_info="",
                    domain_name=_DOMAIN,
                    role=UserRole.USER,
                    resource_policy="usage-user-policy",
                    allowed_client_ip=None,
                    totp_key=None,
                    domain_id=owner.domain_id,
                )
            )
            for project_id, name in (
                (owner.project_a, "project-a"),
                (owner.project_b, "project-b"),
            ):
                db_sess.add(
                    ProjectRow(
                        id=project_id,
                        name=name,
                        description="",
                        is_active=True,
                        domain_name=_DOMAIN,
                        total_resource_slots=ResourceSlot(),
                        allowed_vfolder_hosts={},
                        resource_policy="usage-project-policy",
                        type=ProjectType.GENERAL,
                    )
                )
            await db_sess.flush()
            db_sess.add(
                KeyPairRow(
                    user=owner.user_id,
                    access_key=owner.access_key,
                    secret_key=SecretValue("usage-secret-key"),
                    is_active=True,
                    is_admin=False,
                    resource_policy="usage-keypair-policy",
                    rate_limit=1000,
                )
            )
            for slot_name, slot_type in (("cpu", "count"), ("mem", "bytes")):
                db_sess.add(ResourceSlotTypeRow(slot_name=slot_name, slot_type=slot_type))
            await db_sess.flush()
            db_sess.add(
                AgentRow(
                    id=_AGENT_ID,
                    status=AgentStatus.ALIVE,
                    status_changed=_PERIOD_START,
                    region="local",
                    scaling_group="default",
                    resource_group_id=owner.resource_group_id,
                    addr="tcp://127.0.0.1:6001",
                    first_contact=_PERIOD_START,
                    lost_at=None,
                    public_host="127.0.0.1",
                    public_key=PublicKey(b"usage-public-key"),
                    version="26.10.0",
                    architecture="x86_64",
                    compute_plugins={},
                    schedulable=True,
                    auto_terminate_abusing_kernel=False,
                )
            )
            await db_sess.commit()
        return owner

    async def _add_kernel(
        self,
        db: ExtendedAsyncSAEngine,
        owner: _Owner,
        *,
        project_id: uuid.UUID,
        session_name: str,
        status: KernelStatus,
        created_at: datetime,
        terminated_at: datetime | None,
        cpu: Decimal | None = None,
    ) -> KernelId:
        """Insert a session with one kernel, and the kernel's cpu allocation when given."""
        session_id = SessionId(uuid.uuid4())
        kernel_id = KernelId(uuid.uuid4())
        async with db.begin_session() as db_sess:
            db_sess.add(
                SessionRow(
                    id=session_id,
                    creation_id=session_id.hex,
                    name=session_name,
                    session_type=SessionTypes.INTERACTIVE,
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                    domain_id=owner.domain_id,
                    domain_name=_DOMAIN,
                    group_id=project_id,
                    user_uuid=owner.user_id,
                    access_key=owner.access_key,
                    tag=None,
                    status=SessionStatus.RUNNING,
                    status_info=None,
                    status_data=None,
                    status_history={},
                    result=SessionResult.UNDEFINED,
                    created_at=created_at,
                    terminated_at=terminated_at,
                    starts_at=None,
                    startup_command=None,
                    callback_url=None,
                    vfolder_mounts=[],
                    environ=None,
                    bootstrap_script=None,
                    use_host_network=False,
                    resource_group_id=owner.resource_group_id,
                    scaling_group_name="default",
                )
            )
            await db_sess.flush()
            db_sess.add(
                KernelRow(
                    id=kernel_id,
                    session_id=session_id,
                    session_type=SessionTypes.INTERACTIVE,
                    domain_name=_DOMAIN,
                    group_id=project_id,
                    user_uuid=owner.user_id,
                    access_key=owner.access_key,
                    cluster_mode=ClusterMode.SINGLE_NODE.value,
                    cluster_size=1,
                    cluster_role="main",
                    cluster_idx=0,
                    local_rank=0,
                    cluster_hostname="main",
                    scaling_group="default",
                    resource_group_id=owner.resource_group_id,
                    image="cr.backend.ai/stable/python:latest",
                    architecture="x86_64",
                    registry="cr.backend.ai",
                    agent=_AGENT_ID,
                    agent_addr="tcp://127.0.0.1:6001",
                    container_id=None,
                    repl_in_port=2000,
                    repl_out_port=2001,
                    stdin_port=2002,
                    stdout_port=2003,
                    use_host_network=False,
                    status=status,
                    status_info=None,
                    status_data=None,
                    status_history={},
                    status_changed=created_at,
                    result=SessionResult.UNDEFINED,
                    created_at=created_at,
                    terminated_at=terminated_at,
                    starts_at=None,
                    occupied_shares={},
                    environ=None,
                    vfolder_mounts=[],
                    attached_devices={},
                    resource_opts=None,
                    preopen_ports=None,
                    bootstrap_script=None,
                    startup_command=None,
                    last_stat=_LAST_STAT,
                )
            )
            await db_sess.flush()
            if cpu is not None:
                db_sess.add(
                    ResourceAllocationRow(
                        kernel_id=kernel_id,
                        slot_name="cpu",
                        requested=cpu,
                        used=cpu,
                        used_at=created_at,
                    )
                )
            await db_sess.commit()
        return kernel_id

    @pytest.fixture
    def valkey_stat(self) -> ValkeyStatClient:
        """Every kernel here carries last_stat, so no live statistics are read."""
        client = MagicMock(spec=ValkeyStatClient)
        client.get_user_kernel_statistics_batch = AsyncMock(return_value=[])
        return client

    async def test_kernel_overlapping_period_comes_with_session_project_and_user(
        self, db: ExtendedAsyncSAEngine, owner: _Owner
    ) -> None:
        kernel_id = await self._add_kernel(
            db,
            owner,
            project_id=owner.project_a,
            session_name="overlapping",
            status=KernelStatus.TERMINATED,
            created_at=_PERIOD_START - timedelta(days=1),
            terminated_at=_PERIOD_START + timedelta(days=1),
        )

        records, _ = await fetch_resource_usage(db, _PERIOD_START, _PERIOD_END)

        assert [record.kernel.id for record in records] == [kernel_id]
        record = records[0]
        assert record.session.name == "overlapping"
        assert record.project is not None
        assert record.project.name == "project-a"
        assert record.user_email == "usage@example.com"
        assert record.full_name == "Usage User"

    async def test_running_kernel_created_before_period_end_is_included(
        self, db: ExtendedAsyncSAEngine, owner: _Owner
    ) -> None:
        kernel_id = await self._add_kernel(
            db,
            owner,
            project_id=owner.project_a,
            session_name="running",
            status=KernelStatus.RUNNING,
            created_at=_PERIOD_START + timedelta(days=3),
            terminated_at=None,
        )

        records, _ = await fetch_resource_usage(db, _PERIOD_START, _PERIOD_END)

        assert [record.kernel.id for record in records] == [kernel_id]

    async def test_kernels_outside_period_or_usage_statuses_are_excluded(
        self, db: ExtendedAsyncSAEngine, owner: _Owner
    ) -> None:
        await self._add_kernel(
            db,
            owner,
            project_id=owner.project_a,
            session_name="ended-before",
            status=KernelStatus.TERMINATED,
            created_at=_PERIOD_START - timedelta(days=5),
            terminated_at=_PERIOD_START - timedelta(days=1),
        )
        await self._add_kernel(
            db,
            owner,
            project_id=owner.project_a,
            session_name="created-after",
            status=KernelStatus.RUNNING,
            created_at=_PERIOD_END + timedelta(days=1),
            terminated_at=None,
        )
        await self._add_kernel(
            db,
            owner,
            project_id=owner.project_a,
            session_name="cancelled",
            status=KernelStatus.CANCELLED,
            created_at=_PERIOD_START + timedelta(days=1),
            terminated_at=_PERIOD_START + timedelta(days=2),
        )

        records, _ = await fetch_resource_usage(db, _PERIOD_START, _PERIOD_END)

        assert records == []

    async def test_allocated_slots_come_from_resource_allocations(
        self, db: ExtendedAsyncSAEngine, owner: _Owner
    ) -> None:
        kernel_id = await self._add_kernel(
            db,
            owner,
            project_id=owner.project_a,
            session_name="allocated",
            status=KernelStatus.RUNNING,
            created_at=_PERIOD_START,
            terminated_at=None,
            cpu=Decimal("2"),
        )

        _, allocated_slots = await fetch_resource_usage(db, _PERIOD_START, _PERIOD_END)

        assert allocated_slots[kernel_id]["cpu"] == Decimal("2")

    async def test_groups_carry_the_joined_values_and_allocations(
        self,
        db: ExtendedAsyncSAEngine,
        owner: _Owner,
        valkey_stat: ValkeyStatClient,
    ) -> None:
        kernel_id = await self._add_kernel(
            db,
            owner,
            project_id=owner.project_a,
            session_name="grouped",
            status=KernelStatus.TERMINATED,
            created_at=_PERIOD_START,
            terminated_at=_PERIOD_START + timedelta(days=2),
            cpu=Decimal("2"),
        )

        records, allocated_slots = await fetch_resource_usage(db, _PERIOD_START, _PERIOD_END)
        groups = await parse_resource_usage_groups(records, allocated_slots, valkey_stat, UTC)

        assert len(groups) == 1
        group = groups[0]
        assert group.kernel_id == kernel_id
        assert group.session_name == "grouped"
        assert group.project_id == owner.project_a
        assert group.project_name == "project-a"
        assert group.user_id == owner.user_id
        assert group.user_email == "usage@example.com"
        assert group.full_name == "Usage User"
        assert group.domain_name == _DOMAIN
        assert group.used_days == 3
        assert group.total_usage.cpu_allocated == 2.0

    async def test_project_filter_keeps_only_the_requested_project_usage(
        self,
        db: ExtendedAsyncSAEngine,
        owner: _Owner,
        valkey_stat: ValkeyStatClient,
    ) -> None:
        await self._add_kernel(
            db,
            owner,
            project_id=owner.project_a,
            session_name="in-a",
            status=KernelStatus.RUNNING,
            created_at=_PERIOD_START,
            terminated_at=None,
            cpu=Decimal("2"),
        )
        await self._add_kernel(
            db,
            owner,
            project_id=owner.project_b,
            session_name="in-b",
            status=KernelStatus.RUNNING,
            created_at=_PERIOD_START,
            terminated_at=None,
            cpu=Decimal("4"),
        )

        records, allocated_slots = await fetch_resource_usage(
            db, _PERIOD_START, _PERIOD_END, project_ids=[owner.project_a]
        )
        groups = await parse_resource_usage_groups(records, allocated_slots, valkey_stat, UTC)
        project_usage, total_usage = parse_total_resource_group(groups)

        assert list(project_usage) == [owner.project_a]
        assert total_usage.cpu_allocated == 2.0
