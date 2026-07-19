"""Real-DB tests for the retention DB source.

Everything runs through the public ``sweep()`` entry point (there is no other
caller-facing operation). Per category with self-contained tables, a seeded
policy drives the sweep and we assert rows past the age boundary are purged
while newer / non-terminal / recently-touched rows are preserved, deletion
advances across batches, unwired categories are skipped, and the per-tick budget
defers the rest.

``sessions`` exercises the ordered kernels->sessions delete with the
remaining-kernel / live-routing NOT EXISTS guards. The terminal-state filter is
validated on the FK-free ``roles`` table via its ``TimestampBoundaryPurgerSpec``
directly; ``login`` and the invitation tables share that exact spec, so they are
not duplicated here.

sweep() derives its threshold from DB ``now``, so fixtures use timestamps
relative to the real current time; every category is seeded with a 30-day policy
so its threshold lands at ~now-30d.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa

from ai.backend.common.events.types import EventDomain
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.actions.types import OperationStatus
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.error_log.types import ErrorLogSeverity
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.retention.types import RetentionCategory, RetentionPurgeResult
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.audit_log.row import AuditLogRow
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointLifecycle, EndpointRow
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
from ai.backend.manager.models.resource_usage_history.row import KernelUsageRecordRow
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
from ai.backend.manager.repositories.retention.purgers import TimestampBoundaryPurgerSpec
from ai.backend.testutils.db import with_tables

_NOW = datetime.now(UTC)
_THRESHOLD = _NOW - timedelta(days=30)
_OLD = _NOW - timedelta(days=400)  # older than threshold -> eligible for purge
_NEW = _NOW - timedelta(days=1)  # newer than threshold -> preserved
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
        spec = TimestampBoundaryPurgerSpec(
            RoleRow,
            RoleRow.deleted_at,
            _THRESHOLD,
            extra_conditions=(RoleRow.status == RoleStatus.DELETED,),
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
    stamp, unwired categories skipped without aborting the tick, per-tick budget
    defers the rest, disabled policies excluded."""

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

    async def test_purges_wired_stamps_swept_and_skips_unwired(
        self, db: ExtendedAsyncSAEngine, db_source: RetentionDBSource
    ) -> None:
        await _insert(
            db,
            [
                EventLogRow(event_name="old", event_domain=EventDomain.SESSION, created_at=_OLD),
                EventLogRow(event_name="recent", event_domain=EventDomain.SESSION, created_at=_NEW),
                _policy_row(RetentionCategory.LOGS),
                # Seeded enabled but not wired yet -> must be skipped, not abort the tick.
                _policy_row(RetentionCategory.DEPLOYMENTS),
            ],
        )

        results = await db_source.sweep()

        assert [r.category for r in results] == [RetentionCategory.LOGS]
        assert results[0].deleted_count == 1  # only the old EventLog row
        assert await _count(db, EventLogRow) == 1
        assert await _swept_at(db, RetentionCategory.LOGS) is not None
        # Skipped category keeps its NULL stamp so it retries once wired.
        assert await _swept_at(db, RetentionCategory.DEPLOYMENTS) is None

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
