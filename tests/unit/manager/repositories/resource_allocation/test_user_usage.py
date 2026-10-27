"""Tests for the resource allocation user usage read against a real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from dateutil.tz import tzutc

from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    DefaultForUnspecified,
    KernelId,
    ResourceSlot,
    SecretKey,
    SessionId,
    SessionResult,
    SessionTypes,
    SlotQuantity,
)
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.dotfile.row import DotfileRow
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.rbac_models.entity_field import EntityFieldRow
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.resource_group.types import ResourceGroupOpts
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_slot.row import (
    AgentResourceRow,
    ResourceAllocationRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.scheduling_history.row import SessionSchedulingHistoryRow
from ai.backend.manager.models.session.row import SessionDependencyRow, SessionRow
from ai.backend.manager.models.session_group.row import SessionGroupRow
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.resource_allocation.provider import (
    ResourceAllocationOpsProvider,
)
from ai.backend.manager.secret.types import SecretValue
from ai.backend.testutils.db import with_tables

_LIMIT_CPU = Decimal("10")
_LIMIT_MEM = Decimal("10240")


@dataclass(frozen=True)
class _Owner:
    domain_id: DomainID
    domain_name: DomainName
    resource_group_id: ResourceGroupID
    resource_group_name: str
    project_id: uuid.UUID
    user_id: UserID
    default_access_key: AccessKey
    other_access_key: AccessKey


def _keypair(access_key: AccessKey, user_id: UserID, policy: str, is_default: bool) -> KeyPairRow:
    return KeyPairRow(
        access_key=access_key,
        secret_key=SecretValue(SecretKey(f"SK{uuid.uuid4().hex}")),
        is_active=True,
        is_admin=False,
        is_default=is_default,
        resource_policy=policy,
        rate_limit=1000,
        num_queries=0,
        user=user_id,
    )


async def _run_session(
    db: ExtendedAsyncSAEngine,
    owner: _Owner,
    access_key: AccessKey,
    cpu: Decimal,
    mem: Decimal,
    session_type: SessionTypes = SessionTypes.INTERACTIVE,
) -> None:
    """Insert a RUNNING single-kernel session with usage-reported allocation rows."""
    session_id = SessionId(uuid.uuid4())
    kernel_id = KernelId(uuid.uuid4())
    now = datetime.now(tzutc())
    async with db.begin_session() as db_sess:
        db_sess.add(
            SessionRow(
                id=session_id,
                name=f"session-{uuid.uuid4().hex[:8]}",
                session_type=session_type,
                domain_id=owner.domain_id,
                domain_name=owner.domain_name,
                group_id=owner.project_id,
                user_uuid=owner.user_id,
                access_key=access_key,
                resource_group_id=owner.resource_group_id,
                scaling_group_name=owner.resource_group_name,
                status=SessionStatus.RUNNING,
                status_info="test",
                cluster_mode=ClusterMode.SINGLE_NODE,
                created_at=now,
                starts_at=now,
                images=["python:3.8"],
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
                session_type=session_type,
                scaling_group=owner.resource_group_name,
                resource_group_id=owner.resource_group_id,
                cluster_idx=0,
                cluster_role="main",
                cluster_hostname=f"kernel-{uuid.uuid4().hex[:8]}",
                image="python:3.8",
                architecture="x86_64",
                registry="docker.io",
                status=KernelStatus.RUNNING,
                status_changed=now,
                domain_name=owner.domain_name,
                group_id=owner.project_id,
                user_uuid=owner.user_id,
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
        for slot_name, amount in [("cpu", cpu), ("mem", mem)]:
            db_sess.add(
                ResourceAllocationRow(
                    kernel_id=kernel_id,
                    slot_name=slot_name,
                    requested=amount,
                    reserved_at=now,
                    used=amount,
                    used_at=now,
                )
            )
        await db_sess.flush()


def _as_dict(quantities: list[SlotQuantity]) -> dict[str, Decimal]:
    result: dict[str, Decimal] = {}
    for q in quantities:
        result[q.slot_name] = Decimal(q.quantity)
    return result


class TestGetUserUsage:
    @pytest.fixture
    async def db(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ResourceGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                RoleRow,
                UserRoleRow,
                UserRow,
                VirtualEntityRow,
                DotfileRow,
                KeyPairRow,
                ProjectRow,
                EntityFieldRow,
                AgentRow,
                ContainerRegistryRow,
                ImageRow,
                SessionGroupRow,
                SessionRow,
                KernelRow,
                ResourceSlotTypeRow,
                ResourceAllocationRow,
                AgentResourceRow,
                SessionDependencyRow,
                SessionSchedulingHistoryRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def owner(self, db: ExtendedAsyncSAEngine) -> _Owner:
        """A user with two keypairs, the first one default, sharing one keypair resource policy."""
        suffix = uuid.uuid4().hex[:8]
        o = _Owner(
            domain_id=DomainID(uuid.uuid4()),
            domain_name=DomainName(f"domain-{suffix}"),
            resource_group_id=ResourceGroupID(uuid.uuid4()),
            resource_group_name=f"rg-{suffix}",
            project_id=uuid.uuid4(),
            user_id=UserID(uuid.uuid4()),
            default_access_key=AccessKey(f"AKIADEF{suffix.upper()}"),
            other_access_key=AccessKey(f"AKIAOTH{suffix.upper()}"),
        )
        async with db.begin_session() as db_sess:
            db_sess.add(DomainRow(id=o.domain_id, name=o.domain_name))
            db_sess.add(
                ResourceGroupRow(
                    id=o.resource_group_id,
                    name=o.resource_group_name,
                    driver="static",
                    scheduler="fifo",
                    scheduler_opts=ResourceGroupOpts(
                        allowed_session_types=[],
                        pending_timeout=timedelta(hours=1),
                        config={},
                    ),
                    driver_opts={},
                    is_active=True,
                )
            )
            db_sess.add(
                UserResourcePolicyRow(
                    name=f"user-policy-{suffix}",
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=3,
                )
            )
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=f"project-policy-{suffix}",
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_network_count=10,
                )
            )
            db_sess.add(
                KeyPairResourcePolicyRow(
                    name=f"keypair-policy-{suffix}",
                    default_for_unspecified=DefaultForUnspecified.LIMITED,
                    total_resource_slots=ResourceSlot({"cpu": _LIMIT_CPU, "mem": _LIMIT_MEM}),
                    max_concurrent_sessions=10,
                    max_containers_per_session=4,
                    idle_timeout=600,
                    max_session_lifetime=0,
                    allowed_vfolder_hosts={},
                )
            )
            for slot_name, slot_type in [("cpu", "count"), ("mem", "bytes")]:
                db_sess.add(ResourceSlotTypeRow(slot_name=slot_name, slot_type=slot_type))
            await db_sess.flush()
            db_sess.add(
                UserRow(
                    uuid=o.user_id,
                    email=f"user-{suffix}@test.com",
                    username=f"user-{suffix}",
                    role=UserRole.USER,
                    status=UserStatus.ACTIVE,
                    domain_name=o.domain_name,
                    resource_policy=f"user-policy-{suffix}",
                    domain_id=o.domain_id,
                )
            )
            db_sess.add(
                ProjectRow(
                    id=o.project_id,
                    name=f"project-{suffix}",
                    description="",
                    is_active=True,
                    domain_name=o.domain_name,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    resource_policy=f"project-policy-{suffix}",
                )
            )
            await db_sess.flush()
            db_sess.add(_keypair(o.default_access_key, o.user_id, f"keypair-policy-{suffix}", True))
            db_sess.add(_keypair(o.other_access_key, o.user_id, f"keypair-policy-{suffix}", False))
            await db_sess.flush()
        return o

    @pytest.fixture
    async def sessions_on_both_keypairs(self, db: ExtendedAsyncSAEngine, owner: _Owner) -> None:
        """cpu 2 / mem 1024 on the default keypair, cpu 3 / mem 2048 on the other one."""
        await _run_session(db, owner, owner.default_access_key, Decimal("2"), Decimal("1024"))
        await _run_session(db, owner, owner.other_access_key, Decimal("3"), Decimal("2048"))

    @pytest.fixture
    async def sftp_session_on_other_keypair(self, db: ExtendedAsyncSAEngine, owner: _Owner) -> None:
        """cpu 1 / mem 512 in a private (SYSTEM) session on the non-default keypair."""
        await _run_session(
            db,
            owner,
            owner.other_access_key,
            Decimal("1"),
            Decimal("512"),
            session_type=SessionTypes.SYSTEM,
        )

    @pytest.fixture
    def ops_provider(self, db: ExtendedAsyncSAEngine) -> ResourceAllocationOpsProvider:
        return ResourceAllocationOpsProvider(db)

    async def test_sums_sessions_from_every_keypair(
        self,
        ops_provider: ResourceAllocationOpsProvider,
        owner: _Owner,
        sessions_on_both_keypairs: None,
    ) -> None:
        async with ops_provider.read_ops() as ops:
            usage = await ops.user_usage(owner.user_id)

        assert _as_dict(usage.used) == {"cpu": Decimal("5"), "mem": Decimal("3072")}
        assert _as_dict(usage.assignable) == {
            "cpu": _LIMIT_CPU - Decimal("5"),
            "mem": _LIMIT_MEM - Decimal("3072"),
        }

    async def test_excludes_private_sessions(
        self,
        ops_provider: ResourceAllocationOpsProvider,
        owner: _Owner,
        sessions_on_both_keypairs: None,
        sftp_session_on_other_keypair: None,
    ) -> None:
        async with ops_provider.read_ops() as ops:
            usage = await ops.user_usage(owner.user_id)

        assert _as_dict(usage.used) == {"cpu": Decimal("5"), "mem": Decimal("3072")}
