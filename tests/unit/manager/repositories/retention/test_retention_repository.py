"""Real-DB tests for the retention DB source.

Everything runs through the public ``sweep()`` entry point (there is no other
caller-facing operation). Per category with self-contained tables, a seeded
policy drives the sweep and we assert rows past the age boundary are purged
while newer / non-terminal / recently-touched rows are preserved, deletion
advances across batches, and the per-tick budget defers the rest.

``sessions`` exercises the ordered kernels->sessions delete with the
remaining-kernel / live-routing NOT EXISTS guards. The terminal-state filter is
validated on the FK-free ``roles`` table via ``RetentionPurgerSpec`` directly;
``login`` and the invitation tables share that exact spec, so they are not
duplicated here. deployments' specs are likewise exercised directly (its
deployment_revisions FK chain makes a full sweep disproportionate).

sweep() derives its threshold from DB ``now``, so fixtures use timestamps
relative to the real current time; every category is seeded with a 30-day policy
so its threshold lands at ~now-30d.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa

from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.events.types import EventDomain
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.schema.deployment import IntOrPercent, ReplicaGroupRolloutSpec
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.actions.types import OperationStatus
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.deployment.types import ReplicaGroupLifecycle
from ai.backend.manager.data.error_log.types import ErrorLogSeverity
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.retention.types import RetentionCategory, RetentionPurgeResult
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.audit_log.row import AuditLogRow
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_policy.row import DeploymentPolicyRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointLifecycle, EndpointRow, EndpointTokenRow
from ai.backend.manager.models.error_logs import ErrorLogRow
from ai.backend.manager.models.event_log.row import EventLogRow
from ai.backend.manager.models.group import GroupRow, ProjectType
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.replica_group_history.row import ReplicaGroupHistoryRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_usage_history.row import (
    DomainUsageBucketRow,
    KernelUsageRecordRow,
    ProjectUsageBucketRow,
    UsageBucketEntryRow,
    UserUsageBucketRow,
)
from ai.backend.manager.models.retention.row import RetentionPolicyRow
from ai.backend.manager.models.routing.row import RouteStatus, RoutingRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.scheduling_history.row import (
    DeploymentHistoryRow,
    KernelSchedulingHistoryRow,
    RouteHistoryRow,
    SessionSchedulingHistoryRow,
)
from ai.backend.manager.models.session import (
    SessionDependencyRow,
    SessionRow,
    SessionStatus,
    SessionTypes,
)
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder.row import VFolderRow
from ai.backend.manager.repositories.base import BatchPurger
from ai.backend.manager.repositories.ops import DBOpsProvider
from ai.backend.manager.repositories.retention.db_source.db_source import RetentionDBSource
from ai.backend.manager.repositories.retention.purgers import RetentionPurgerSpec
from ai.backend.testutils.db import with_tables

_NOW = datetime.now(UTC)
_THRESHOLD = _NOW - timedelta(days=30)
_OLD = _NOW - timedelta(days=400)  # older than threshold -> eligible for purge
_NEW = _NOW - timedelta(days=1)  # newer than threshold -> preserved
_OLD_DATE = _OLD.date()  # date-typed boundary for usage_buckets (period_end is Date)
_NEW_DATE = _NEW.date()
_RETENTION_DAYS = 30


@dataclass
class _Scope:
    """Shared parent rows a session/kernel/routing all hang off of."""

    domain_name: str = "retention-domain"
    domain_id: DomainID = field(default_factory=lambda: DomainID(uuid.uuid4()))
    group_id: uuid.UUID = field(default_factory=uuid.uuid4)
    user_uuid: uuid.UUID = field(default_factory=uuid.uuid4)
    sgroup_name: str = "retention-sgroup"
    sgroup_id: ResourceGroupID = field(default_factory=lambda: ResourceGroupID(uuid.uuid4()))
    policy_name: str = "retention-project-policy"
    user_policy_name: str = "retention-user-policy"


async def _insert(engine: ExtendedAsyncSAEngine, rows: list[Base]) -> None:
    async with engine.begin_session() as sess:
        sess.add_all(rows)


async def _count(engine: ExtendedAsyncSAEngine, row_class: type[Base]) -> int:
    async with engine.begin_readonly_session() as sess:
        result = await sess.execute(sa.select(sa.func.count()).select_from(row_class))
        return int(result.scalar_one())


async def _swept_at(engine: ExtendedAsyncSAEngine, category: RetentionCategory) -> datetime | None:
    async with engine.begin_readonly_session() as sess:
        result = await sess.execute(
            sa.select(RetentionPolicyRow.last_swept_at).where(
                RetentionPolicyRow.category == category
            )
        )
        return result.scalar_one()


def _policy_row(
    category: RetentionCategory,
    *,
    enabled: bool = True,
    last_swept_at: datetime | None = None,
) -> RetentionPolicyRow:
    return RetentionPolicyRow(
        category=category,
        retention_period=timedelta(days=_RETENTION_DAYS),
        enabled=enabled,
        last_swept_at=last_swept_at,
    )


def _make_db_source(
    engine: ExtendedAsyncSAEngine,
    *,
    batch_size: int = 100,
    per_tick_budget: int | None = None,
) -> RetentionDBSource:
    config_provider = MagicMock()
    config_provider.config.retention.batch_size = batch_size
    config_provider.config.retention.per_tick_budget = per_tick_budget
    return RetentionDBSource(DBOpsProvider(engine), config_provider)


async def _sweep_category(
    engine: ExtendedAsyncSAEngine,
    category: RetentionCategory,
    *,
    batch_size: int = 100,
) -> RetentionPurgeResult:
    """Seed an enabled policy for ``category`` and run the sweep; return its result.

    The DB holds only this one policy, so the sweep processes exactly this
    category and always includes it in the results (wired categories are never
    skipped, even at zero deletions).
    """
    await _insert(engine, [_policy_row(category)])
    results = await _make_db_source(engine, batch_size=batch_size).sweep()
    return next(r for r in results if r.category is category)


@pytest.fixture
def db_source(database_connection: ExtendedAsyncSAEngine) -> RetentionDBSource:
    return _make_db_source(database_connection)


class TestLogsRetention:
    """logs: created_at group across three tables; error_logs ignores flags."""

    @pytest.fixture
    async def db(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncIterator[ExtendedAsyncSAEngine]:
        # error_logs carries a (nullable) FK to users, so the users table must
        # exist even though the inserted rows leave it NULL.
        async with with_tables(
            database_connection,
            [
                DomainRow,
                UserResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRow,
                KeyPairRow,
                EventLogRow,
                AuditLogRow,
                ErrorLogRow,
                RetentionPolicyRow,
            ],
        ):
            yield database_connection

    async def test_purges_old_rows_across_all_log_tables(self, db: ExtendedAsyncSAEngine) -> None:
        await _insert(
            db,
            [
                EventLogRow(event_name="old", event_domain=EventDomain.SESSION, created_at=_OLD),
                EventLogRow(event_name="new", event_domain=EventDomain.SESSION, created_at=_NEW),
                AuditLogRow(
                    entity_type="t",
                    operation="op",
                    action_id=uuid.uuid4(),
                    description="old",
                    created_at=_OLD,
                    status=OperationStatus.SUCCESS,
                ),
                self._error_log(message="old", created_at=_OLD),
            ],
        )

        result = await _sweep_category(db, RetentionCategory.LOGS)

        assert result.category is RetentionCategory.LOGS
        assert result.deleted_count == 3  # one old row from each of the three tables
        assert await _count(db, EventLogRow) == 1
        assert await _count(db, AuditLogRow) == 0
        assert await _count(db, ErrorLogRow) == 0

    async def test_error_logs_ignores_read_and_cleared_flags(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        await _insert(
            db,
            [
                # Past boundary but flagged read+cleared -> still deleted.
                self._error_log(message="old", created_at=_OLD, is_read=True, is_cleared=True),
                # Newer than boundary -> preserved regardless of flags.
                self._error_log(message="new", created_at=_NEW),
            ],
        )

        result = await _sweep_category(db, RetentionCategory.LOGS)

        assert result.deleted_count == 1
        assert await _count(db, ErrorLogRow) == 1

    def _error_log(
        self,
        *,
        message: str,
        created_at: datetime,
        is_read: bool = False,
        is_cleared: bool = False,
    ) -> ErrorLogRow:
        return ErrorLogRow(
            severity=ErrorLogSeverity.ERROR,
            source="s",
            message=message,
            context_lang="en",
            context_env={},
            is_read=is_read,
            is_cleared=is_cleared,
            created_at=created_at,
        )


class TestReconcileHistoryRetention:
    """reconcile_history: boundary is updated_at, so a recently-retried row
    (old created_at, fresh updated_at) survives. Also exercises chunked
    delete-and-advance on FK-free tables."""

    @pytest.fixture
    async def db(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncIterator[ExtendedAsyncSAEngine]:
        async with with_tables(
            database_connection,
            [
                SessionSchedulingHistoryRow,
                KernelSchedulingHistoryRow,
                DeploymentHistoryRow,
                RouteHistoryRow,
                ReplicaGroupHistoryRow,
                RetentionPolicyRow,
            ],
        ):
            yield database_connection

    async def test_uses_updated_at_not_created_at(self, db: ExtendedAsyncSAEngine) -> None:
        await _insert(
            db,
            [
                # Stale: both timestamps old -> deleted.
                self._session_history(message="stale", created_at=_OLD, updated_at=_OLD),
                # Recently retried: old created_at but fresh updated_at -> preserved.
                self._session_history(message="retried", created_at=_OLD, updated_at=_NEW),
                self._kernel_history(message="stale", created_at=_OLD, updated_at=_OLD),
            ],
        )

        result = await _sweep_category(db, RetentionCategory.RECONCILE_HISTORY)

        assert result.deleted_count == 2
        assert await _count(db, SessionSchedulingHistoryRow) == 1
        assert await _count(db, KernelSchedulingHistoryRow) == 0

    async def test_advances_across_batches_smaller_than_backlog(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        await _insert(
            db,
            [
                self._session_history(message=f"s{i}", created_at=_OLD, updated_at=_OLD)
                for i in range(5)
            ],
        )

        result = await _sweep_category(db, RetentionCategory.RECONCILE_HISTORY, batch_size=2)

        assert result.deleted_count == 5  # batch_size=2 drains all 5 via advance
        assert await _count(db, SessionSchedulingHistoryRow) == 0

    def _session_history(
        self, *, message: str, created_at: datetime, updated_at: datetime
    ) -> SessionSchedulingHistoryRow:
        return SessionSchedulingHistoryRow(
            session_id=uuid.uuid4(),
            phase="p",
            result="r",
            message=message,
            created_at=created_at,
            updated_at=updated_at,
        )

    def _kernel_history(
        self, *, message: str, created_at: datetime, updated_at: datetime
    ) -> KernelSchedulingHistoryRow:
        return KernelSchedulingHistoryRow(
            kernel_id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            phase="p",
            result="r",
            message=message,
            created_at=created_at,
            updated_at=updated_at,
        )


class TestUsageRecordsRetention:
    """usage_records: simple period_end boundary."""

    @pytest.fixture
    async def db(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncIterator[ExtendedAsyncSAEngine]:
        async with with_tables(database_connection, [KernelUsageRecordRow, RetentionPolicyRow]):
            yield database_connection

    async def test_purges_by_period_end(self, db: ExtendedAsyncSAEngine) -> None:
        await _insert(db, [_usage_record(period_end=_OLD), _usage_record(period_end=_NEW)])

        result = await _sweep_category(db, RetentionCategory.USAGE_RECORDS)

        assert result.deleted_count == 1
        assert await _count(db, KernelUsageRecordRow) == 1


def _usage_record(*, period_end: datetime) -> KernelUsageRecordRow:
    return KernelUsageRecordRow(
        kernel_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        user_uuid=uuid.uuid4(),
        project_id=uuid.uuid4(),
        domain_name="default",
        resource_group="default",
        resource_group_id=ResourceGroupID(uuid.uuid4()),
        period_start=period_end - timedelta(hours=1),
        period_end=period_end,
        resource_usage=ResourceSlot(),
    )


class TestTerminalStateFilter:
    """The terminal-status + boundary filter used by roles_invitations/login,
    validated on the FK-free roles table via its purger spec."""

    @pytest.fixture
    async def db(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncIterator[ExtendedAsyncSAEngine]:
        async with with_tables(database_connection, [RoleRow]):
            yield database_connection

    async def test_only_deleted_rows_past_boundary_are_purged(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        await _insert(
            db,
            [
                RoleRow(name="deleted-old", status=RoleStatus.DELETED, deleted_at=_OLD),
                RoleRow(name="deleted-new", status=RoleStatus.DELETED, deleted_at=_NEW),
                # Active role: never deleted, deleted_at is NULL -> preserved.
                RoleRow(name="active", status=RoleStatus.ACTIVE),
            ],
        )
        spec = RetentionPurgerSpec(
            RoleRow,
            RoleRow.deleted_at,
            _THRESHOLD,
            conditions=(RoleRow.status == RoleStatus.DELETED,),
        )

        async with DBOpsProvider(db).write_ops() as w:
            result = await w.batch_purge(BatchPurger(spec=spec, batch_size=100))

        assert result.deleted_count == 1
        remaining = {name for (name,) in await self._role_names(db)}
        assert remaining == {"deleted-new", "active"}

    async def _role_names(self, engine: ExtendedAsyncSAEngine) -> list[tuple[str]]:
        async with engine.begin_readonly_session() as sess:
            result = await sess.execute(sa.select(RoleRow.name))
            return [tuple(r) for r in result.all()]


class TestSessionsRetention:
    """sessions: ordered kernels->sessions delete, guarded by remaining-kernel
    and live-routing NOT EXISTS so a sweep never trips the plain/RESTRICT FKs."""

    @pytest.fixture
    async def db(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncIterator[ExtendedAsyncSAEngine]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ProjectResourcePolicyRow,
                UserResourcePolicyRow,
                KeyPairResourcePolicyRow,
                ScalingGroupRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                SessionRow,
                AgentRow,
                ContainerRegistryRow,
                ImageRow,
                KernelRow,
                VFolderRow,
                EndpointRow,
                ReplicaGroupRow,
                RoutingRow,
                SessionDependencyRow,
                RetentionPolicyRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def scope(self, db: ExtendedAsyncSAEngine) -> _Scope:
        scope = _Scope()
        async with db.begin_session() as sess:
            sess.add(
                ProjectResourcePolicyRow(
                    name=scope.policy_name,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_network_count=0,
                )
            )
            sess.add(
                UserResourcePolicyRow(
                    name=scope.user_policy_name,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
            sess.add(
                DomainRow(
                    id=scope.domain_id,
                    name=scope.domain_name,
                    description=None,
                    is_active=True,
                )
            )
            sess.add(
                ScalingGroupRow(
                    name=scope.sgroup_name,
                    id=scope.sgroup_id,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    scheduler_opts=ScalingGroupOpts(),
                )
            )
            sess.add(
                UserRow(
                    uuid=scope.user_uuid,
                    username="retention-user",
                    email="retention@example.com",
                    password=PasswordInfo(
                        password="pw",
                        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                        rounds=100_000,
                        salt_size=32,
                    ),
                    need_password_change=False,
                    full_name="Retention User",
                    description="",
                    status=UserStatus.ACTIVE,
                    status_info="",
                    domain_name=scope.domain_name,
                    role=UserRole.USER,
                    resource_policy=scope.user_policy_name,
                )
            )
            sess.add(
                GroupRow(
                    id=scope.group_id,
                    name="retention-group",
                    description=None,
                    is_active=True,
                    domain_name=scope.domain_name,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    dotfiles=b"\x90",
                    resource_policy=scope.policy_name,
                    type=ProjectType.GENERAL,
                )
            )
        return scope

    async def _add_session(
        self,
        db: ExtendedAsyncSAEngine,
        scope: _Scope,
        *,
        status: SessionStatus,
        terminated_at: datetime | None,
    ) -> uuid.UUID:
        session_id = uuid.uuid4()
        async with db.begin_session() as sess:
            sess.add(
                SessionRow(
                    id=session_id,
                    name=f"session-{session_id}",
                    session_type=SessionTypes.INTERACTIVE,
                    cluster_mode="single-node",
                    cluster_size=1,
                    domain_name=scope.domain_name,
                    domain_id=scope.domain_id,
                    group_id=scope.group_id,
                    scaling_group_name=scope.sgroup_name,
                    resource_group_id=scope.sgroup_id,
                    user_uuid=scope.user_uuid,
                    occupying_slots=ResourceSlot({}),
                    requested_slots=ResourceSlot({}),
                    status=status,
                    status_info="",
                    target_sgroup_names=[],
                    vfolder_mounts=[],
                    environ={},
                    terminated_at=terminated_at,
                )
            )
        return session_id

    async def _add_kernel(
        self,
        db: ExtendedAsyncSAEngine,
        scope: _Scope,
        session_id: uuid.UUID,
        *,
        status: KernelStatus,
        terminated_at: datetime | None,
    ) -> None:
        async with db.begin_session() as sess:
            sess.add(
                KernelRow(
                    session_id=session_id,
                    domain_name=scope.domain_name,
                    group_id=scope.group_id,
                    user_uuid=scope.user_uuid,
                    scaling_group=scope.sgroup_name,
                    resource_group_id=scope.sgroup_id,
                    occupied_slots=ResourceSlot({}),
                    requested_slots=ResourceSlot({}),
                    occupied_shares={},
                    vfolder_mounts=[],
                    status=status,
                    repl_in_port=0,
                    repl_out_port=0,
                    stdin_port=0,
                    stdout_port=0,
                    terminated_at=terminated_at,
                )
            )

    async def _add_routing_for(
        self, db: ExtendedAsyncSAEngine, scope: _Scope, session_id: uuid.UUID
    ) -> None:
        async with db.begin_session() as sess:
            endpoint_id = uuid.uuid4()
            sess.add(
                EndpointRow(
                    id=endpoint_id,
                    name=f"endpoint-{endpoint_id}",
                    created_user=scope.user_uuid,
                    session_owner=scope.user_uuid,
                    domain=scope.domain_name,
                    project=scope.group_id,
                    resource_group=scope.sgroup_name,
                    lifecycle_stage=EndpointLifecycle.DESTROYED,
                    replicas=0,
                )
            )
            await sess.flush()
            sess.add(
                RoutingRow(
                    id=uuid.uuid4(),
                    endpoint=endpoint_id,
                    session=session_id,
                    session_owner=scope.user_uuid,
                    domain=scope.domain_name,
                    project=scope.group_id,
                    status=RouteStatus.RUNNING,
                    traffic_ratio=1.0,
                    revision=uuid.uuid4(),
                )
            )

    async def test_deletes_old_session_after_its_kernels(
        self, db: ExtendedAsyncSAEngine, scope: _Scope
    ) -> None:
        session_id = await self._add_session(
            db, scope, status=SessionStatus.TERMINATED, terminated_at=_OLD
        )
        await self._add_kernel(
            db, scope, session_id, status=KernelStatus.TERMINATED, terminated_at=_OLD
        )
        await self._add_kernel(
            db, scope, session_id, status=KernelStatus.CANCELLED, terminated_at=_OLD
        )

        result = await _sweep_category(db, RetentionCategory.SESSIONS)

        assert result.deleted_count == 3  # 2 kernels + 1 session
        assert await _count(db, KernelRow) == 0
        assert await _count(db, SessionRow) == 0

    async def test_live_routing_skips_session_without_error(
        self, db: ExtendedAsyncSAEngine, scope: _Scope
    ) -> None:
        session_id = await self._add_session(
            db, scope, status=SessionStatus.TERMINATED, terminated_at=_OLD
        )
        await self._add_routing_for(db, scope, session_id)

        result = await _sweep_category(db, RetentionCategory.SESSIONS)

        assert result.deleted_count == 0
        assert await _count(db, SessionRow) == 1  # RESTRICT-referenced session preserved

    async def test_recent_kernel_defers_its_session(
        self, db: ExtendedAsyncSAEngine, scope: _Scope
    ) -> None:
        session_id = await self._add_session(
            db, scope, status=SessionStatus.TERMINATED, terminated_at=_OLD
        )
        # Kernel terminated inside the boundary: it survives, so its session is
        # held back this sweep instead of failing the plain FK.
        await self._add_kernel(
            db, scope, session_id, status=KernelStatus.TERMINATED, terminated_at=_NEW
        )

        result = await _sweep_category(db, RetentionCategory.SESSIONS)

        assert result.deleted_count == 0
        assert await _count(db, KernelRow) == 1
        assert await _count(db, SessionRow) == 1

    async def test_preserves_recent_and_nonterminal_sessions(
        self, db: ExtendedAsyncSAEngine, scope: _Scope
    ) -> None:
        await self._add_session(db, scope, status=SessionStatus.TERMINATED, terminated_at=_NEW)
        await self._add_session(db, scope, status=SessionStatus.RUNNING, terminated_at=None)

        result = await _sweep_category(db, RetentionCategory.SESSIONS)

        assert result.deleted_count == 0
        assert await _count(db, SessionRow) == 2

    async def test_cascades_session_dependencies(
        self, db: ExtendedAsyncSAEngine, scope: _Scope
    ) -> None:
        dependant = await self._add_session(
            db, scope, status=SessionStatus.TERMINATED, terminated_at=_OLD
        )
        dependency = await self._add_session(
            db, scope, status=SessionStatus.TERMINATED, terminated_at=_OLD
        )
        async with db.begin_session() as sess:
            sess.add(SessionDependencyRow(session_id=dependant, depends_on=dependency))

        result = await _sweep_category(db, RetentionCategory.SESSIONS)

        assert result.deleted_count == 2
        assert await _count(db, SessionRow) == 0
        assert await _count(db, SessionDependencyRow) == 0  # cascaded with the sessions


class TestSweep:
    """sweep() orchestration across policies: policy-driven purge + last_swept_at
    stamp, per-tick budget defers the rest, disabled policies excluded."""

    @pytest.fixture
    async def db(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncIterator[ExtendedAsyncSAEngine]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                UserResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRow,
                KeyPairRow,
                EventLogRow,
                AuditLogRow,
                ErrorLogRow,
                KernelUsageRecordRow,
                RetentionPolicyRow,
            ],
        ):
            yield database_connection

    async def test_purges_enabled_categories_and_stamps_swept(
        self, db: ExtendedAsyncSAEngine, db_source: RetentionDBSource
    ) -> None:
        await _insert(
            db,
            [
                EventLogRow(event_name="old", event_domain=EventDomain.SESSION, created_at=_OLD),
                EventLogRow(event_name="recent", event_domain=EventDomain.SESSION, created_at=_NEW),
                _usage_record(period_end=_OLD),
                _policy_row(RetentionCategory.LOGS),
                _policy_row(RetentionCategory.USAGE_RECORDS),
            ],
        )

        results = await db_source.sweep()

        assert {r.category for r in results} == {
            RetentionCategory.LOGS,
            RetentionCategory.USAGE_RECORDS,
        }
        assert await _count(db, EventLogRow) == 1  # old purged, recent kept
        assert await _count(db, KernelUsageRecordRow) == 0
        assert await _swept_at(db, RetentionCategory.LOGS) is not None
        assert await _swept_at(db, RetentionCategory.USAGE_RECORDS) is not None

    async def test_per_tick_budget_defers_remaining_categories(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        db_source = _make_db_source(db, per_tick_budget=1)
        already_swept = _NEW
        await _insert(
            db,
            [
                EventLogRow(event_name="a", event_domain=EventDomain.SESSION, created_at=_OLD),
                EventLogRow(event_name="b", event_domain=EventDomain.SESSION, created_at=_OLD),
                _usage_record(period_end=_OLD),
                # LOGS never swept -> ordered first; USAGE_RECORDS swept recently -> second.
                _policy_row(RetentionCategory.LOGS),
                _policy_row(RetentionCategory.USAGE_RECORDS, last_swept_at=already_swept),
            ],
        )

        results = await db_source.sweep()

        # LOGS drains 2 rows, hitting the budget; USAGE_RECORDS is deferred.
        assert [r.category for r in results] == [RetentionCategory.LOGS]
        assert await _count(db, KernelUsageRecordRow) == 1
        assert await _swept_at(db, RetentionCategory.USAGE_RECORDS) == already_swept

    async def test_disabled_policy_is_not_swept(
        self, db: ExtendedAsyncSAEngine, db_source: RetentionDBSource
    ) -> None:
        await _insert(
            db,
            [
                EventLogRow(event_name="old", event_domain=EventDomain.SESSION, created_at=_OLD),
                _policy_row(RetentionCategory.LOGS, enabled=False),
            ],
        )

        results = await db_source.sweep()

        assert results == []
        assert await _count(db, EventLogRow) == 1  # disabled -> row preserved


class TestDeploymentsRetention:
    """deployments: DESTROYED endpoints past destroyed_at drive the purge; CASCADE
    children (deployment_policies) follow at the DB; endpoint_tokens clear on
    their own expiry. Specs are exercised directly to avoid the
    deployment_revisions image/vfolder/runtime FK chain; the FK-less-child form
    is checked against endpoint_tokens standing in for deployment_revisions."""

    @pytest.fixture
    async def db(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncIterator[ExtendedAsyncSAEngine]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ProjectResourcePolicyRow,
                ScalingGroupRow,
                GroupRow,
                EndpointRow,
                DeploymentPolicyRow,
                EndpointTokenRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def scope(self, db: ExtendedAsyncSAEngine) -> _Scope:
        scope = _Scope()
        async with db.begin_session() as sess:
            sess.add(
                ProjectResourcePolicyRow(
                    name=scope.policy_name,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_network_count=0,
                )
            )
            sess.add(
                DomainRow(
                    id=scope.domain_id, name=scope.domain_name, description=None, is_active=True
                )
            )
            sess.add(
                ScalingGroupRow(
                    name=scope.sgroup_name,
                    id=scope.sgroup_id,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    scheduler_opts=ScalingGroupOpts(),
                )
            )
            sess.add(
                GroupRow(
                    id=scope.group_id,
                    name="retention-group",
                    description=None,
                    is_active=True,
                    domain_name=scope.domain_name,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    dotfiles=b"\x90",
                    resource_policy=scope.policy_name,
                    type=ProjectType.GENERAL,
                )
            )
        return scope

    async def _add_endpoint(
        self,
        db: ExtendedAsyncSAEngine,
        scope: _Scope,
        *,
        lifecycle: EndpointLifecycle,
        destroyed_at: datetime | None,
    ) -> DeploymentID:
        endpoint_id = DeploymentID(uuid.uuid4())
        async with db.begin_session() as sess:
            sess.add(
                EndpointRow(
                    id=endpoint_id,
                    name=f"endpoint-{endpoint_id}",
                    created_user=scope.user_uuid,
                    session_owner=scope.user_uuid,
                    domain=scope.domain_name,
                    project=scope.group_id,
                    resource_group=scope.sgroup_name,
                    lifecycle_stage=lifecycle,
                    replicas=0,
                    destroyed_at=destroyed_at,
                )
            )
        return endpoint_id

    async def _add_deployment_policy(
        self, db: ExtendedAsyncSAEngine, endpoint_id: DeploymentID
    ) -> None:
        async with db.begin_session() as sess:
            sess.add(DeploymentPolicyRow(endpoint=endpoint_id, strategy=DeploymentStrategy.ROLLING))

    async def _add_token(
        self,
        db: ExtendedAsyncSAEngine,
        scope: _Scope,
        *,
        endpoint_id: DeploymentID,
        expires_at: datetime | None,
    ) -> None:
        async with db.begin_session() as sess:
            sess.add(
                EndpointTokenRow(
                    id=uuid.uuid4(),
                    token=f"tok-{uuid.uuid4()}",
                    endpoint=endpoint_id,
                    session_owner=scope.user_uuid,
                    domain=scope.domain_name,
                    project=scope.group_id,
                    expires_at=expires_at,
                )
            )

    async def _purge_endpoints(self, db: ExtendedAsyncSAEngine) -> int:
        spec = RetentionPurgerSpec(
            EndpointRow,
            EndpointRow.destroyed_at,
            _THRESHOLD,
            conditions=(EndpointRow.lifecycle_stage == EndpointLifecycle.DESTROYED,),
        )
        async with DBOpsProvider(db).write_ops() as w:
            result = await w.batch_purge(BatchPurger(spec=spec, batch_size=100))
        return result.deleted_count

    async def test_destroyed_endpoint_past_boundary_cascades_children(
        self, db: ExtendedAsyncSAEngine, scope: _Scope
    ) -> None:
        endpoint_id = await self._add_endpoint(
            db, scope, lifecycle=EndpointLifecycle.DESTROYED, destroyed_at=_OLD
        )
        await self._add_deployment_policy(db, endpoint_id)

        deleted = await self._purge_endpoints(db)

        assert deleted == 1  # the endpoint; its policy cascades at the DB level
        assert await _count(db, EndpointRow) == 0
        assert await _count(db, DeploymentPolicyRow) == 0

    async def test_preserves_living_and_recent_endpoints(
        self, db: ExtendedAsyncSAEngine, scope: _Scope
    ) -> None:
        await self._add_endpoint(db, scope, lifecycle=EndpointLifecycle.READY, destroyed_at=None)
        await self._add_endpoint(
            db, scope, lifecycle=EndpointLifecycle.DESTROYED, destroyed_at=_NEW
        )

        deleted = await self._purge_endpoints(db)

        assert deleted == 0
        assert await _count(db, EndpointRow) == 2

    async def test_endpoint_tokens_purged_by_expiry(
        self, db: ExtendedAsyncSAEngine, scope: _Scope
    ) -> None:
        # endpoint id is irrelevant to expiry-based purge; use throwaway ids.
        await self._add_token(db, scope, endpoint_id=DeploymentID(uuid.uuid4()), expires_at=_OLD)
        await self._add_token(db, scope, endpoint_id=DeploymentID(uuid.uuid4()), expires_at=_NEW)
        # A never-expiring token (NULL expires_at) is preserved.
        await self._add_token(db, scope, endpoint_id=DeploymentID(uuid.uuid4()), expires_at=None)

        spec = RetentionPurgerSpec(EndpointTokenRow, EndpointTokenRow.expires_at, _THRESHOLD)
        async with DBOpsProvider(db).write_ops() as w:
            result = await w.batch_purge(BatchPurger(spec=spec, batch_size=100))

        assert result.deleted_count == 1
        assert await _count(db, EndpointTokenRow) == 2

    async def test_fk_less_child_deleted_by_destroyed_endpoint(
        self, db: ExtendedAsyncSAEngine, scope: _Scope
    ) -> None:
        # endpoint_tokens stand in for deployment_revisions: an FK-less child
        # keyed by endpoint id, deleted when its parent endpoint is DESTROYED and
        # past the boundary.
        destroyed_id = await self._add_endpoint(
            db, scope, lifecycle=EndpointLifecycle.DESTROYED, destroyed_at=_OLD
        )
        living_id = await self._add_endpoint(
            db, scope, lifecycle=EndpointLifecycle.READY, destroyed_at=None
        )
        await self._add_token(db, scope, endpoint_id=destroyed_id, expires_at=_NEW)
        await self._add_token(db, scope, endpoint_id=living_id, expires_at=_NEW)

        spec = RetentionPurgerSpec(
            EndpointTokenRow,
            EndpointRow.destroyed_at,
            _THRESHOLD,
            match_column=EndpointTokenRow.endpoint,
            source_key=EndpointRow.id,
            source_conditions=(EndpointRow.lifecycle_stage == EndpointLifecycle.DESTROYED,),
        )
        async with DBOpsProvider(db).write_ops() as w:
            result = await w.batch_purge(BatchPurger(spec=spec, batch_size=100))

        assert result.deleted_count == 1  # only the destroyed endpoint's child
        assert await _count(db, EndpointTokenRow) == 1  # the living endpoint's survives


class TestDeploymentsTerminalChildCleanup:
    """deployments also clears terminal routings and replica_groups on their own
    updated_at boundary. Endpoint cascade only reaches children of a purged
    endpoint, so a route/group retired under a still-live endpoint must be swept
    independently."""

    @pytest.fixture
    async def db(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncIterator[ExtendedAsyncSAEngine]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ProjectResourcePolicyRow,
                UserResourcePolicyRow,
                KeyPairResourcePolicyRow,
                ScalingGroupRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                SessionRow,
                EndpointRow,
                ReplicaGroupRow,
                RoutingRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def scope(self, db: ExtendedAsyncSAEngine) -> _Scope:
        scope = _Scope()
        async with db.begin_session() as sess:
            sess.add(
                ProjectResourcePolicyRow(
                    name=scope.policy_name,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_network_count=0,
                )
            )
            sess.add(
                UserResourcePolicyRow(
                    name=scope.user_policy_name,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
            sess.add(
                DomainRow(
                    id=scope.domain_id, name=scope.domain_name, description=None, is_active=True
                )
            )
            sess.add(
                ScalingGroupRow(
                    name=scope.sgroup_name,
                    id=scope.sgroup_id,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    scheduler_opts=ScalingGroupOpts(),
                )
            )
            sess.add(
                UserRow(
                    uuid=scope.user_uuid,
                    username="retention-user",
                    email="retention@example.com",
                    password=PasswordInfo(
                        password="pw",
                        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                        rounds=100_000,
                        salt_size=32,
                    ),
                    need_password_change=False,
                    full_name="Retention User",
                    description="",
                    status=UserStatus.ACTIVE,
                    status_info="",
                    domain_name=scope.domain_name,
                    role=UserRole.USER,
                    resource_policy=scope.user_policy_name,
                )
            )
            sess.add(
                GroupRow(
                    id=scope.group_id,
                    name="retention-group",
                    description=None,
                    is_active=True,
                    domain_name=scope.domain_name,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    dotfiles=b"\x90",
                    resource_policy=scope.policy_name,
                    type=ProjectType.GENERAL,
                )
            )
        return scope

    async def _add_live_endpoint(self, db: ExtendedAsyncSAEngine, scope: _Scope) -> DeploymentID:
        endpoint_id = DeploymentID(uuid.uuid4())
        async with db.begin_session() as sess:
            sess.add(
                EndpointRow(
                    id=endpoint_id,
                    name=f"endpoint-{endpoint_id}",
                    created_user=scope.user_uuid,
                    session_owner=scope.user_uuid,
                    domain=scope.domain_name,
                    project=scope.group_id,
                    resource_group=scope.sgroup_name,
                    lifecycle_stage=EndpointLifecycle.READY,
                    replicas=0,
                )
            )
        return endpoint_id

    async def _add_routing(
        self,
        db: ExtendedAsyncSAEngine,
        scope: _Scope,
        endpoint_id: DeploymentID,
        *,
        status: RouteStatus,
        updated_at: datetime,
    ) -> None:
        async with db.begin_session() as sess:
            sess.add(
                RoutingRow(
                    id=uuid.uuid4(),
                    endpoint=endpoint_id,
                    session=None,
                    session_owner=scope.user_uuid,
                    domain=scope.domain_name,
                    project=scope.group_id,
                    status=status,
                    traffic_ratio=1.0,
                    revision=uuid.uuid4(),
                    updated_at=updated_at,
                )
            )

    async def _add_replica_group(
        self,
        db: ExtendedAsyncSAEngine,
        endpoint_id: DeploymentID,
        *,
        lifecycle: ReplicaGroupLifecycle,
        updated_at: datetime,
    ) -> None:
        async with db.begin_session() as sess:
            sess.add(
                ReplicaGroupRow(
                    id=uuid.uuid4(),
                    deployment_id=endpoint_id,
                    lifecycle=lifecycle,
                    rollout=ReplicaGroupRolloutSpec(
                        max_surge=IntOrPercent(count=1),
                        max_unavailable=IntOrPercent(count=0),
                    ),
                    updated_at=updated_at,
                )
            )

    async def test_terminal_routings_purged_under_live_endpoint(
        self, db: ExtendedAsyncSAEngine, scope: _Scope
    ) -> None:
        endpoint_id = await self._add_live_endpoint(db, scope)
        await self._add_routing(
            db, scope, endpoint_id, status=RouteStatus.TERMINATED, updated_at=_OLD
        )
        await self._add_routing(
            db, scope, endpoint_id, status=RouteStatus.FAILED_TO_START, updated_at=_OLD
        )
        # Running route -> not terminal, preserved.
        await self._add_routing(db, scope, endpoint_id, status=RouteStatus.RUNNING, updated_at=_OLD)
        # Terminal but inside the boundary -> held back this sweep.
        await self._add_routing(
            db, scope, endpoint_id, status=RouteStatus.TERMINATED, updated_at=_NEW
        )

        spec = RetentionPurgerSpec(
            RoutingRow,
            RoutingRow.updated_at,
            _THRESHOLD,
            conditions=(RoutingRow.status.in_(RouteStatus.terminal_statuses()),),
        )
        async with DBOpsProvider(db).write_ops() as w:
            result = await w.batch_purge(BatchPurger(spec=spec, batch_size=100))

        assert result.deleted_count == 2  # terminated + failed-to-start, both old
        assert await _count(db, RoutingRow) == 2  # running + recently-terminated
        assert await _count(db, EndpointRow) == 1  # the live endpoint is untouched

    async def test_terminal_replica_groups_purged_under_live_endpoint(
        self, db: ExtendedAsyncSAEngine, scope: _Scope
    ) -> None:
        endpoint_id = await self._add_live_endpoint(db, scope)
        await self._add_replica_group(
            db, endpoint_id, lifecycle=ReplicaGroupLifecycle.DRAINED, updated_at=_OLD
        )
        await self._add_replica_group(
            db, endpoint_id, lifecycle=ReplicaGroupLifecycle.FAILED, updated_at=_OLD
        )
        # Active group -> not terminal, preserved.
        await self._add_replica_group(
            db, endpoint_id, lifecycle=ReplicaGroupLifecycle.STABLE, updated_at=_OLD
        )
        # Drained but inside the boundary -> held back this sweep.
        await self._add_replica_group(
            db, endpoint_id, lifecycle=ReplicaGroupLifecycle.DRAINED, updated_at=_NEW
        )

        spec = RetentionPurgerSpec(
            ReplicaGroupRow,
            ReplicaGroupRow.updated_at,
            _THRESHOLD,
            conditions=(ReplicaGroupRow.lifecycle.in_(ReplicaGroupLifecycle.terminal_statuses()),),
        )
        async with DBOpsProvider(db).write_ops() as w:
            result = await w.batch_purge(BatchPurger(spec=spec, batch_size=100))

        assert result.deleted_count == 2  # drained + failed, both old
        assert await _count(db, ReplicaGroupRow) == 2  # stable + recently-drained
        assert await _count(db, EndpointRow) == 1  # the live endpoint is untouched


class TestUsageBucketsRetention:
    """usage_buckets: each bucket kind purged on its own period_end, with its
    FK-less usage_bucket_entries (keyed by bucket_id + bucket_type) drained first
    so no orphan entry remains. FK-free, so it runs end-to-end through sweep()."""

    @pytest.fixture
    async def db(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncIterator[ExtendedAsyncSAEngine]:
        async with with_tables(
            database_connection,
            [
                DomainUsageBucketRow,
                ProjectUsageBucketRow,
                UserUsageBucketRow,
                UsageBucketEntryRow,
                RetentionPolicyRow,
            ],
        ):
            yield database_connection

    async def _add_domain_bucket(self, db: ExtendedAsyncSAEngine, *, period_end: date) -> uuid.UUID:
        bucket_id = uuid.uuid4()
        async with db.begin_session() as sess:
            sess.add(
                DomainUsageBucketRow(
                    id=bucket_id,
                    domain_name="d",
                    resource_group="rg",
                    resource_group_id=ResourceGroupID(uuid.uuid4()),
                    period_start=period_end - timedelta(days=1),
                    period_end=period_end,
                )
            )
        return bucket_id

    async def _add_project_bucket(
        self, db: ExtendedAsyncSAEngine, *, period_end: date
    ) -> uuid.UUID:
        bucket_id = uuid.uuid4()
        async with db.begin_session() as sess:
            sess.add(
                ProjectUsageBucketRow(
                    id=bucket_id,
                    project_id=uuid.uuid4(),
                    domain_name="d",
                    resource_group="rg",
                    resource_group_id=ResourceGroupID(uuid.uuid4()),
                    period_start=period_end - timedelta(days=1),
                    period_end=period_end,
                )
            )
        return bucket_id

    async def _add_user_bucket(self, db: ExtendedAsyncSAEngine, *, period_end: date) -> uuid.UUID:
        bucket_id = uuid.uuid4()
        async with db.begin_session() as sess:
            sess.add(
                UserUsageBucketRow(
                    id=bucket_id,
                    user_uuid=uuid.uuid4(),
                    project_id=uuid.uuid4(),
                    domain_name="d",
                    resource_group="rg",
                    resource_group_id=ResourceGroupID(uuid.uuid4()),
                    period_start=period_end - timedelta(days=1),
                    period_end=period_end,
                )
            )
        return bucket_id

    async def _add_entry(
        self, db: ExtendedAsyncSAEngine, *, bucket_id: uuid.UUID, bucket_type: str, slot: str
    ) -> None:
        async with db.begin_session() as sess:
            sess.add(
                UsageBucketEntryRow(
                    bucket_id=bucket_id,
                    bucket_type=bucket_type,
                    slot_name=slot,
                    resource_usage=Decimal("1"),
                    duration_seconds=1,
                    capacity=Decimal("1"),
                )
            )

    async def test_old_buckets_and_their_entries_purged_no_orphan(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        old_bucket = await self._add_domain_bucket(db, period_end=_OLD_DATE)
        await self._add_entry(db, bucket_id=old_bucket, bucket_type="domain", slot="cpu")
        await self._add_entry(db, bucket_id=old_bucket, bucket_type="domain", slot="mem")
        new_bucket = await self._add_domain_bucket(db, period_end=_NEW_DATE)
        await self._add_entry(db, bucket_id=new_bucket, bucket_type="domain", slot="cpu")

        result = await _sweep_category(db, RetentionCategory.USAGE_BUCKETS)

        assert result.deleted_count == 3  # 2 entries + 1 bucket
        assert await _count(db, DomainUsageBucketRow) == 1
        assert await _count(db, UsageBucketEntryRow) == 1  # only the live bucket's entry

    async def test_all_three_bucket_kinds_purged(self, db: ExtendedAsyncSAEngine) -> None:
        domain_bucket = await self._add_domain_bucket(db, period_end=_OLD_DATE)
        await self._add_entry(db, bucket_id=domain_bucket, bucket_type="domain", slot="cpu")
        project_bucket = await self._add_project_bucket(db, period_end=_OLD_DATE)
        await self._add_entry(db, bucket_id=project_bucket, bucket_type="project", slot="cpu")
        user_bucket = await self._add_user_bucket(db, period_end=_OLD_DATE)
        await self._add_entry(db, bucket_id=user_bucket, bucket_type="user", slot="cpu")

        result = await _sweep_category(db, RetentionCategory.USAGE_BUCKETS)

        assert result.deleted_count == 6  # 3 buckets + 3 entries
        assert await _count(db, DomainUsageBucketRow) == 0
        assert await _count(db, ProjectUsageBucketRow) == 0
        assert await _count(db, UserUsageBucketRow) == 0
        assert await _count(db, UsageBucketEntryRow) == 0


class TestCatalogCompleteness:
    def test_every_category_is_wired(self) -> None:
        # The sweep iterates enabled policies of any category, so every
        # RetentionCategory must resolve to a purger spec set.
        catalog = RetentionDBSource._catalog(_THRESHOLD)
        assert set(catalog) == set(RetentionCategory)
