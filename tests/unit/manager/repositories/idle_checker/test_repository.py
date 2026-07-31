from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import UTC, datetime

import pytest
import sqlalchemy as sa

from ai.backend.common.data.idle_checker.types import (
    CheckerType,
    IdleCheckerSpec,
    IdleCheckPhase,
    SessionLifetimeSpec,
)
from ai.backend.common.data.permission.types import ScopeType
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.idle_checker import IdleCheckerAssignmentID, IdleCheckerID
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import (
    ClusterMode,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.errors.idle_checker import (
    IdleCheckerAssignmentNotFound,
    IdleCheckerExclusionTargetMismatch,
)
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.idle_checker.row import (
    IdleCheckerBindingRow,
    IdleCheckerRow,
    SessionIdleCheckRow,
)
from ai.backend.manager.models.resource_policy import ProjectResourcePolicyRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.idle_checker.repository import IdleCheckerRepository
from ai.backend.manager.repositories.idle_checker.types import (
    IdleJudgmentData,
    SessionIdleCheckExclusionUpdate,
    SessionIdleCheckPair,
    SessionIdleCheckTarget,
)
from ai.backend.manager.repositories.ops import DBOpsProvider
from ai.backend.testutils.db import with_tables


@dataclass(frozen=True)
class ScopeFixture:
    domain_name: str
    domain_id: DomainID
    project_id: uuid.UUID
    scaling_group_name: str
    scaling_group_id: ResourceGroupID


@dataclass(frozen=True)
class ExpiredCheckSessionData:
    session_id: SessionId
    first_checker_id: IdleCheckerID
    second_checker_id: IdleCheckerID
    first_expire_at: datetime
    second_expire_at: datetime


@dataclass(frozen=True)
class JudgmentRows:
    active_session_id: SessionId
    idle_session_id: SessionId
    not_checked_session_id: SessionId
    ready_to_check_session_id: SessionId
    idle_expired_session_id: SessionId
    session_without_row_id: SessionId
    terminated_session_id: SessionId
    second_terminated_session_id: SessionId
    checker_id: IdleCheckerID


def _expired_check_scope_rows(
    scope: ScopeFixture,
) -> tuple[ProjectResourcePolicyRow, DomainRow, GroupRow, ScalingGroupRow]:
    return (
        ProjectResourcePolicyRow(
            name=f"{scope.domain_name}-policy",
            max_vfolder_count=10,
            max_quota_scope_size=1024,
            max_network_count=10,
        ),
        DomainRow(
            id=scope.domain_id,
            name=scope.domain_name,
            description=None,
            is_active=True,
        ),
        GroupRow(
            id=scope.project_id,
            name=f"{scope.domain_name}-project",
            description=None,
            is_active=True,
            domain_name=scope.domain_name,
            resource_policy=f"{scope.domain_name}-policy",
        ),
        ScalingGroupRow(
            id=scope.scaling_group_id,
            name=scope.scaling_group_name,
            description=None,
            is_active=True,
            is_public=True,
            driver="static",
            driver_opts={},
            scheduler="fifo",
            use_host_network=False,
        ),
    )


def _expired_check_session_row(
    scope: ScopeFixture,
    session_id: SessionId,
    status: SessionStatus,
    session_type: SessionTypes = SessionTypes.INTERACTIVE,
) -> SessionRow:
    return SessionRow(
        id=session_id,
        creation_id=str(session_id)[:32],
        name=f"session-{session_id}",
        session_type=session_type,
        cluster_mode=ClusterMode.SINGLE_NODE,
        cluster_size=1,
        domain_name=scope.domain_name,
        domain_id=scope.domain_id,
        resource_group_id=scope.scaling_group_id,
        group_id=scope.project_id,
        user_uuid=uuid.uuid4(),
        access_key=None,
        tag=None,
        status=status,
        status_info=None,
        status_data=None,
        status_history={},
        result=SessionResult.UNDEFINED,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        terminated_at=None,
        starts_at=datetime(2026, 1, 1, tzinfo=UTC),
        startup_command=None,
        callback_url=None,
        occupying_slots=ResourceSlot({"cpu": "1"}),
        requested_slots=ResourceSlot({"cpu": "1"}),
        vfolder_mounts=[],
        environ=None,
        bootstrap_script=None,
        use_host_network=False,
        scaling_group_name=scope.scaling_group_name,
    )


def _expired_check_checker_row(checker_id: IdleCheckerID) -> IdleCheckerRow:
    return IdleCheckerRow(
        id=checker_id,
        name=f"checker-{checker_id}",
        description=None,
        target_session_types=[SessionTypes.INTERACTIVE],
        initial_grace_period_seconds=45,
        spec=IdleCheckerSpec(
            type=CheckerType.SESSION_LIFETIME,
            session_lifetime=SessionLifetimeSpec(max_lifetime_seconds=3600),
        ),
    )


def _expired_check_scope_fixture(prefix: str) -> ScopeFixture:
    return ScopeFixture(
        domain_name=f"{prefix}-domain",
        domain_id=DomainID(uuid.uuid4()),
        project_id=uuid.uuid4(),
        scaling_group_name=f"{prefix}-sgroup",
        scaling_group_id=ResourceGroupID(uuid.uuid4()),
    )


class TestFetchJudgmentBatch:
    @pytest.fixture
    async def database(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                ProjectResourcePolicyRow,
                DomainRow,
                GroupRow,
                ScalingGroupRow,
                SessionRow,
                IdleCheckerRow,
                IdleCheckerBindingRow,
                SessionIdleCheckRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def repository(self, database: ExtendedAsyncSAEngine) -> IdleCheckerRepository:
        return IdleCheckerRepository(DBOpsProvider(database))

    @pytest.fixture
    async def judgment_rows(
        self,
        database: ExtendedAsyncSAEngine,
    ) -> JudgmentRows:
        scope = _expired_check_scope_fixture("judgment")
        active_session_id = SessionId(uuid.uuid4())
        idle_session_id = SessionId(uuid.uuid4())
        not_checked_session_id = SessionId(uuid.uuid4())
        ready_to_check_session_id = SessionId(uuid.uuid4())
        idle_expired_session_id = SessionId(uuid.uuid4())
        session_without_row_id = SessionId(uuid.uuid4())
        terminated_session_id = SessionId(uuid.uuid4())
        second_terminated_session_id = SessionId(uuid.uuid4())
        checker_id = IdleCheckerID(uuid.uuid4())
        session_specs = (
            (active_session_id, SessionStatus.RUNNING),
            (idle_session_id, SessionStatus.RUNNING),
            (not_checked_session_id, SessionStatus.RUNNING),
            (ready_to_check_session_id, SessionStatus.RUNNING),
            (idle_expired_session_id, SessionStatus.RUNNING),
            (session_without_row_id, SessionStatus.RUNNING),
            (terminated_session_id, SessionStatus.TERMINATED),
            (second_terminated_session_id, SessionStatus.TERMINATED),
        )
        check_specs = (
            (active_session_id, IdleCheckPhase.ACTIVE),
            (idle_session_id, IdleCheckPhase.IDLE),
            (not_checked_session_id, IdleCheckPhase.NOT_CHECKED),
            (ready_to_check_session_id, IdleCheckPhase.READY_TO_CHECK),
            (idle_expired_session_id, IdleCheckPhase.IDLE_EXPIRED),
            (terminated_session_id, IdleCheckPhase.ACTIVE),
            (second_terminated_session_id, IdleCheckPhase.ACTIVE),
        )
        async with database.begin_session() as db_sess:
            for scope_row in _expired_check_scope_rows(scope):
                db_sess.add(scope_row)
            for session_id, status in session_specs:
                db_sess.add(_expired_check_session_row(scope, session_id, status))
            db_sess.add(_expired_check_checker_row(checker_id))
            await db_sess.flush()
            db_sess.add(
                IdleCheckerBindingRow(
                    scope_type=ScopeType.DOMAIN.value,
                    scope_id=scope.domain_id,
                    idle_checker_id=checker_id,
                    enabled=True,
                )
            )
            for session_id, phase in check_specs:
                db_sess.add(
                    SessionIdleCheckRow(
                        session_id=session_id,
                        idle_checker_id=checker_id,
                        expire_at=(
                            None
                            if phase in (IdleCheckPhase.NOT_CHECKED, IdleCheckPhase.READY_TO_CHECK)
                            else datetime(2026, 2, 1, tzinfo=UTC)
                        ),
                        last_status=phase,
                        last_message=f"{phase.value} judgment",
                    )
                )
        return JudgmentRows(
            active_session_id=active_session_id,
            idle_session_id=idle_session_id,
            not_checked_session_id=not_checked_session_id,
            ready_to_check_session_id=ready_to_check_session_id,
            idle_expired_session_id=idle_expired_session_id,
            session_without_row_id=session_without_row_id,
            terminated_session_id=terminated_session_id,
            second_terminated_session_id=second_terminated_session_id,
            checker_id=checker_id,
        )

    async def test_returns_ready_active_and_idle_rows(
        self,
        repository: IdleCheckerRepository,
        judgment_rows: JudgmentRows,
    ) -> None:
        batch = await repository.fetch_judgment_batch([SessionStatus.RUNNING])

        pairs = {
            (assignment.session.session_id, assignment.checker.checker_id)
            for assignment in batch.assignments
        }
        assert pairs == {
            (judgment_rows.ready_to_check_session_id, judgment_rows.checker_id),
            (judgment_rows.active_session_id, judgment_rows.checker_id),
            (judgment_rows.idle_session_id, judgment_rows.checker_id),
        }
        expire_at_by_session = {
            assignment.session.session_id: assignment.session.expire_at
            for assignment in batch.assignments
        }
        assert expire_at_by_session[judgment_rows.ready_to_check_session_id] is None
        assert expire_at_by_session[judgment_rows.active_session_id] == datetime(
            2026, 2, 1, tzinfo=UTC
        )
        assert expire_at_by_session[judgment_rows.idle_session_id] == datetime(
            2026, 2, 1, tzinfo=UTC
        )

    async def test_excludes_non_judgment_phases(
        self,
        repository: IdleCheckerRepository,
        judgment_rows: JudgmentRows,
    ) -> None:
        batch = await repository.fetch_judgment_batch([SessionStatus.RUNNING])

        session_ids = {assignment.session.session_id for assignment in batch.assignments}
        assert judgment_rows.not_checked_session_id not in session_ids
        assert judgment_rows.idle_expired_session_id not in session_ids

    async def test_marks_not_checked_row_ready_to_check(
        self,
        database: ExtendedAsyncSAEngine,
        repository: IdleCheckerRepository,
        judgment_rows: JudgmentRows,
    ) -> None:
        pair = SessionIdleCheckPair(
            judgment_rows.not_checked_session_id,
            judgment_rows.checker_id,
        )

        await repository.batch_update_session_idle_check_phase(
            [pair],
            from_phase=IdleCheckPhase.NOT_CHECKED,
            to_phase=IdleCheckPhase.READY_TO_CHECK,
        )

        async with database.begin_readonly_session() as db_sess:
            row = await db_sess.get(
                SessionIdleCheckRow,
                (pair.session_id, pair.checker_id),
            )
        assert row is not None
        assert row.last_status is IdleCheckPhase.READY_TO_CHECK
        assert row.expire_at is None

    async def test_does_not_overwrite_row_that_is_no_longer_not_checked(
        self,
        database: ExtendedAsyncSAEngine,
        repository: IdleCheckerRepository,
        judgment_rows: JudgmentRows,
    ) -> None:
        pair = SessionIdleCheckPair(
            judgment_rows.active_session_id,
            judgment_rows.checker_id,
        )

        await repository.batch_update_session_idle_check_phase(
            [pair],
            from_phase=IdleCheckPhase.NOT_CHECKED,
            to_phase=IdleCheckPhase.READY_TO_CHECK,
        )

        async with database.begin_readonly_session() as db_sess:
            row = await db_sess.get(
                SessionIdleCheckRow,
                (pair.session_id, pair.checker_id),
            )
        assert row is not None
        assert row.last_status is IdleCheckPhase.ACTIVE

    async def test_transitions_between_injected_phases(
        self,
        database: ExtendedAsyncSAEngine,
        repository: IdleCheckerRepository,
        judgment_rows: JudgmentRows,
    ) -> None:
        pair = SessionIdleCheckPair(
            judgment_rows.active_session_id,
            judgment_rows.checker_id,
        )

        await repository.batch_update_session_idle_check_phase(
            [pair],
            from_phase=IdleCheckPhase.ACTIVE,
            to_phase=IdleCheckPhase.IDLE,
        )

        async with database.begin_readonly_session() as db_sess:
            row = await db_sess.get(
                SessionIdleCheckRow,
                (pair.session_id, pair.checker_id),
            )
        assert row is not None
        assert row.last_status is IdleCheckPhase.IDLE

    async def test_marks_existing_row_when_batch_contains_missing_pair(
        self,
        database: ExtendedAsyncSAEngine,
        repository: IdleCheckerRepository,
        judgment_rows: JudgmentRows,
    ) -> None:
        existing_pair = SessionIdleCheckPair(
            judgment_rows.not_checked_session_id,
            judgment_rows.checker_id,
        )
        missing_pair = SessionIdleCheckPair(
            SessionId(uuid.uuid4()),
            judgment_rows.checker_id,
        )

        await repository.batch_update_session_idle_check_phase(
            [existing_pair, missing_pair],
            from_phase=IdleCheckPhase.NOT_CHECKED,
            to_phase=IdleCheckPhase.READY_TO_CHECK,
        )

        async with database.begin_readonly_session() as db_sess:
            row = await db_sess.get(
                SessionIdleCheckRow,
                (existing_pair.session_id, existing_pair.checker_id),
            )
            missing_row = await db_sess.get(
                SessionIdleCheckRow,
                (missing_pair.session_id, missing_pair.checker_id),
            )
        assert row is not None
        assert row.last_status is IdleCheckPhase.READY_TO_CHECK
        assert missing_row is None

    async def test_fetches_only_not_checked_rows_for_initial_grace_period(
        self,
        repository: IdleCheckerRepository,
        judgment_rows: JudgmentRows,
    ) -> None:
        batch = await repository.fetch_initial_grace_period_checks([SessionStatus.RUNNING])

        assert [check.pair for check in batch.checks] == [
            SessionIdleCheckPair(
                judgment_rows.not_checked_session_id,
                judgment_rows.checker_id,
            )
        ]
        assert batch.checks[0].initial_grace_period_seconds == 45

    async def test_applies_all_judgment_batches_with_distinct_messages(
        self,
        database: ExtendedAsyncSAEngine,
        repository: IdleCheckerRepository,
        judgment_rows: JudgmentRows,
    ) -> None:
        expire_at = datetime(2026, 3, 1, tzinfo=UTC)
        idle_expired = [
            IdleJudgmentData(
                session_id=judgment_rows.active_session_id,
                checker_id=judgment_rows.checker_id,
                status=IdleCheckPhase.IDLE_EXPIRED,
                expire_at=expire_at,
                message="idle expired 1",
            ),
            IdleJudgmentData(
                session_id=judgment_rows.not_checked_session_id,
                checker_id=judgment_rows.checker_id,
                status=IdleCheckPhase.IDLE_EXPIRED,
                expire_at=expire_at,
                message="idle expired 2",
            ),
            IdleJudgmentData(
                session_id=judgment_rows.terminated_session_id,
                checker_id=judgment_rows.checker_id,
                status=IdleCheckPhase.IDLE_EXPIRED,
                expire_at=expire_at,
                message="idle expired 3",
            ),
        ]
        idle = [
            IdleJudgmentData(
                session_id=judgment_rows.idle_session_id,
                checker_id=judgment_rows.checker_id,
                status=IdleCheckPhase.IDLE,
                expire_at=expire_at,
                message="idle 1",
            ),
            IdleJudgmentData(
                session_id=judgment_rows.ready_to_check_session_id,
                checker_id=judgment_rows.checker_id,
                status=IdleCheckPhase.IDLE,
                expire_at=expire_at,
                message="idle 2",
            ),
        ]
        active = [
            IdleJudgmentData(
                session_id=judgment_rows.second_terminated_session_id,
                checker_id=judgment_rows.checker_id,
                status=IdleCheckPhase.ACTIVE,
                expire_at=expire_at,
                message="active 1",
            ),
        ]

        judgments = [*idle_expired, *idle, *active]
        await repository.batch_apply_session_idle_check_judgments(judgments)

        async with database.begin_readonly_session() as db_sess:
            for judgment in judgments:
                row = await db_sess.get(
                    SessionIdleCheckRow,
                    (judgment.session_id, judgment.checker_id),
                )
                assert row is not None
                assert row.last_status is judgment.status
                assert row.expire_at == judgment.expire_at
                assert row.last_message == judgment.message

    async def test_accepts_empty_judgment_batch(
        self,
        repository: IdleCheckerRepository,
    ) -> None:
        await repository.batch_apply_session_idle_check_judgments([])

    async def test_never_touches_idle_expired_row(
        self,
        database: ExtendedAsyncSAEngine,
        repository: IdleCheckerRepository,
        judgment_rows: JudgmentRows,
    ) -> None:
        await repository.batch_apply_session_idle_check_judgments([
            IdleJudgmentData(
                session_id=judgment_rows.idle_expired_session_id,
                checker_id=judgment_rows.checker_id,
                status=IdleCheckPhase.ACTIVE,
                expire_at=datetime(2026, 3, 1, tzinfo=UTC),
                message="activity detected",
            )
        ])

        async with database.begin_readonly_session() as db_sess:
            row = await db_sess.get(
                SessionIdleCheckRow,
                (judgment_rows.idle_expired_session_id, judgment_rows.checker_id),
            )
        assert row is not None
        assert row.last_status is IdleCheckPhase.IDLE_EXPIRED
        assert row.last_message == f"{IdleCheckPhase.IDLE_EXPIRED.value} judgment"
        assert row.expire_at == datetime(2026, 2, 1, tzinfo=UTC)

    async def test_ignores_missing_pair_without_insert(
        self,
        database: ExtendedAsyncSAEngine,
        repository: IdleCheckerRepository,
        judgment_rows: JudgmentRows,
    ) -> None:
        missing_session_id = SessionId(uuid.uuid4())

        await repository.batch_apply_session_idle_check_judgments([
            IdleJudgmentData(
                session_id=missing_session_id,
                checker_id=judgment_rows.checker_id,
                status=IdleCheckPhase.ACTIVE,
                expire_at=datetime(2026, 3, 1, tzinfo=UTC),
                message="activity detected",
            )
        ])

        async with database.begin_readonly_session() as db_sess:
            row = await db_sess.get(
                SessionIdleCheckRow,
                (missing_session_id, judgment_rows.checker_id),
            )
        assert row is None

    async def test_excludes_session_without_idle_check_row(
        self,
        repository: IdleCheckerRepository,
        judgment_rows: JudgmentRows,
    ) -> None:
        batch = await repository.fetch_judgment_batch([SessionStatus.RUNNING])

        session_ids = {assignment.session.session_id for assignment in batch.assignments}
        assert judgment_rows.session_without_row_id not in session_ids

    async def test_excludes_sessions_not_in_target_statuses(
        self,
        repository: IdleCheckerRepository,
        judgment_rows: JudgmentRows,
    ) -> None:
        batch = await repository.fetch_judgment_batch([SessionStatus.RUNNING])

        session_ids = {assignment.session.session_id for assignment in batch.assignments}
        assert judgment_rows.terminated_session_id not in session_ids

    async def test_fetches_desired_and_current_assignment_pairs(
        self,
        repository: IdleCheckerRepository,
        judgment_rows: JudgmentRows,
    ) -> None:
        assignments = await repository.fetch_session_idle_check_assignments([SessionStatus.RUNNING])

        assert set(assignments.desired_pairs) == {
            SessionIdleCheckPair(session_id, judgment_rows.checker_id)
            for session_id in (
                judgment_rows.active_session_id,
                judgment_rows.idle_session_id,
                judgment_rows.not_checked_session_id,
                judgment_rows.ready_to_check_session_id,
                judgment_rows.idle_expired_session_id,
                judgment_rows.session_without_row_id,
            )
        }
        assert set(assignments.current_pairs) == {
            SessionIdleCheckPair(session_id, judgment_rows.checker_id)
            for session_id in (
                judgment_rows.active_session_id,
                judgment_rows.idle_session_id,
                judgment_rows.not_checked_session_id,
                judgment_rows.ready_to_check_session_id,
                judgment_rows.idle_expired_session_id,
            )
        }
        assert assignments.now.tzinfo is not None

    async def test_creates_missing_assignment_as_not_checked(
        self,
        database: ExtendedAsyncSAEngine,
        repository: IdleCheckerRepository,
        judgment_rows: JudgmentRows,
    ) -> None:
        pair = SessionIdleCheckPair(
            judgment_rows.session_without_row_id,
            judgment_rows.checker_id,
        )

        await repository.sync_session_idle_check_assignments([pair], [])

        async with database.begin_readonly_session() as db_sess:
            row = await db_sess.get(
                SessionIdleCheckRow,
                (pair.session_id, pair.checker_id),
            )
        assert row is not None
        assert row.expire_at is None
        assert row.last_status is IdleCheckPhase.NOT_CHECKED
        assert row.last_message == "Not checked yet."

    async def test_disabled_binding_deletes_non_expired_rows(
        self,
        database: ExtendedAsyncSAEngine,
        repository: IdleCheckerRepository,
        judgment_rows: JudgmentRows,
    ) -> None:
        async with database.begin_session() as db_sess:
            await db_sess.execute(sa.update(IdleCheckerBindingRow).values(enabled=False))
        assignment_snapshot = await repository.fetch_session_idle_check_assignments([
            SessionStatus.RUNNING
        ])
        obsolete_pairs = set(assignment_snapshot.current_pairs) - set(
            assignment_snapshot.desired_pairs
        )

        await repository.sync_session_idle_check_assignments([], list(obsolete_pairs))

        async with database.begin_readonly_session() as db_sess:
            non_expired_rows = (
                await db_sess.scalars(
                    sa.select(SessionIdleCheckRow).where(
                        SessionIdleCheckRow.session_id.in_({
                            judgment_rows.active_session_id,
                            judgment_rows.idle_session_id,
                            judgment_rows.not_checked_session_id,
                        })
                    )
                )
            ).all()
        assert non_expired_rows == []

    async def test_disabled_binding_preserves_idle_expired_row(
        self,
        database: ExtendedAsyncSAEngine,
        repository: IdleCheckerRepository,
        judgment_rows: JudgmentRows,
    ) -> None:
        async with database.begin_session() as db_sess:
            await db_sess.execute(sa.update(IdleCheckerBindingRow).values(enabled=False))
        assignment_snapshot = await repository.fetch_session_idle_check_assignments([
            SessionStatus.RUNNING
        ])
        obsolete_pairs = set(assignment_snapshot.current_pairs) - set(
            assignment_snapshot.desired_pairs
        )

        await repository.sync_session_idle_check_assignments([], list(obsolete_pairs))

        async with database.begin_readonly_session() as db_sess:
            expired_row = await db_sess.get(
                SessionIdleCheckRow,
                (
                    judgment_rows.idle_expired_session_id,
                    judgment_rows.checker_id,
                ),
            )
        assert expired_row is not None
        assert expired_row.last_status is IdleCheckPhase.IDLE_EXPIRED

    async def test_reenabled_binding_creates_fresh_not_checked_row(
        self,
        database: ExtendedAsyncSAEngine,
        repository: IdleCheckerRepository,
        judgment_rows: JudgmentRows,
    ) -> None:
        async with database.begin_session() as db_sess:
            await db_sess.execute(sa.update(IdleCheckerBindingRow).values(enabled=False))
        assignment_snapshot = await repository.fetch_session_idle_check_assignments([
            SessionStatus.RUNNING
        ])
        obsolete_pairs = set(assignment_snapshot.current_pairs) - set(
            assignment_snapshot.desired_pairs
        )
        await repository.sync_session_idle_check_assignments([], list(obsolete_pairs))

        async with database.begin_session() as db_sess:
            await db_sess.execute(sa.update(IdleCheckerBindingRow).values(enabled=True))
        assignment_snapshot = await repository.fetch_session_idle_check_assignments([
            SessionStatus.RUNNING
        ])
        missing_pairs = set(assignment_snapshot.desired_pairs) - set(
            assignment_snapshot.current_pairs
        )

        await repository.sync_session_idle_check_assignments(list(missing_pairs), [])

        async with database.begin_readonly_session() as db_sess:
            recreated_row = await db_sess.get(
                SessionIdleCheckRow,
                (
                    judgment_rows.active_session_id,
                    judgment_rows.checker_id,
                ),
            )
        assert recreated_row is not None
        assert recreated_row.last_status is IdleCheckPhase.NOT_CHECKED
        assert recreated_row.expire_at is None

    async def test_delete_rechecks_expired_status_after_assignment_fetch(
        self,
        database: ExtendedAsyncSAEngine,
        repository: IdleCheckerRepository,
        judgment_rows: JudgmentRows,
    ) -> None:
        pair = SessionIdleCheckPair(
            judgment_rows.active_session_id,
            judgment_rows.checker_id,
        )
        assignments = await repository.fetch_session_idle_check_assignments([SessionStatus.RUNNING])
        assert pair in assignments.current_pairs
        async with database.begin_session() as db_sess:
            await db_sess.execute(
                sa.update(SessionIdleCheckRow)
                .where(
                    SessionIdleCheckRow.session_id == pair.session_id,
                    SessionIdleCheckRow.idle_checker_id == pair.checker_id,
                )
                .values(last_status=IdleCheckPhase.IDLE_EXPIRED)
            )

        await repository.sync_session_idle_check_assignments([], [pair])

        async with database.begin_readonly_session() as db_sess:
            row = await db_sess.get(
                SessionIdleCheckRow,
                (pair.session_id, pair.checker_id),
            )
        assert row is not None
        assert row.last_status is IdleCheckPhase.IDLE_EXPIRED

    async def test_deletes_assignment_after_batch_boundary(
        self,
        database: ExtendedAsyncSAEngine,
        repository: IdleCheckerRepository,
        judgment_rows: JudgmentRows,
    ) -> None:
        pair_to_delete = SessionIdleCheckPair(
            judgment_rows.active_session_id,
            judgment_rows.checker_id,
        )
        pairs_to_delete = [
            SessionIdleCheckPair(
                SessionId(uuid.uuid4()),
                IdleCheckerID(uuid.uuid4()),
            )
            for _ in range(1000)
        ]
        pairs_to_delete.append(pair_to_delete)

        await repository.sync_session_idle_check_assignments([], pairs_to_delete)

        async with database.begin_readonly_session() as db_sess:
            row = await db_sess.get(
                SessionIdleCheckRow,
                (pair_to_delete.session_id, pair_to_delete.checker_id),
            )
        assert row is None


class TestFetchExpiredIdleChecks:
    @pytest.fixture
    async def database(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                ProjectResourcePolicyRow,
                DomainRow,
                GroupRow,
                ScalingGroupRow,
                SessionRow,
                IdleCheckerRow,
                SessionIdleCheckRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def repository(self, database: ExtendedAsyncSAEngine) -> IdleCheckerRepository:
        return IdleCheckerRepository(DBOpsProvider(database))

    @pytest.fixture
    async def expired_check_session(
        self,
        database: ExtendedAsyncSAEngine,
    ) -> ExpiredCheckSessionData:
        scope = _expired_check_scope_fixture("expired-check")
        session_id = SessionId(uuid.uuid4())
        first_checker_id = IdleCheckerID(uuid.uuid4())
        second_checker_id = IdleCheckerID(uuid.uuid4())
        first_expire_at = datetime(2026, 1, 1, tzinfo=UTC)
        second_expire_at = datetime(2100, 1, 1, tzinfo=UTC)
        async with database.begin_session() as db_sess:
            for scope_row in _expired_check_scope_rows(scope):
                db_sess.add(scope_row)
            db_sess.add(_expired_check_session_row(scope, session_id, SessionStatus.RUNNING))
            db_sess.add(_expired_check_checker_row(first_checker_id))
            db_sess.add(_expired_check_checker_row(second_checker_id))
            await db_sess.flush()
            db_sess.add(
                SessionIdleCheckRow(
                    session_id=session_id,
                    idle_checker_id=first_checker_id,
                    expire_at=first_expire_at,
                    last_status=IdleCheckPhase.IDLE_EXPIRED,
                    last_message="Judged expired.",
                )
            )
            db_sess.add(
                SessionIdleCheckRow(
                    session_id=session_id,
                    idle_checker_id=second_checker_id,
                    expire_at=second_expire_at,
                    last_status=IdleCheckPhase.IDLE_EXPIRED,
                    last_message="Judged expired.",
                )
            )
        return ExpiredCheckSessionData(
            session_id=session_id,
            first_checker_id=first_checker_id,
            second_checker_id=second_checker_id,
            first_expire_at=first_expire_at,
            second_expire_at=second_expire_at,
        )

    @pytest.fixture
    async def session_with_elapsed_deadline_still_idle(
        self,
        database: ExtendedAsyncSAEngine,
    ) -> SessionId:
        scope = _expired_check_scope_fixture("elapsed-deadline-still-idle")
        session_id = SessionId(uuid.uuid4())
        checker_id = IdleCheckerID(uuid.uuid4())
        async with database.begin_session() as db_sess:
            for scope_row in _expired_check_scope_rows(scope):
                db_sess.add(scope_row)
            db_sess.add(_expired_check_session_row(scope, session_id, SessionStatus.RUNNING))
            db_sess.add(_expired_check_checker_row(checker_id))
            await db_sess.flush()
            db_sess.add(
                SessionIdleCheckRow(
                    session_id=session_id,
                    idle_checker_id=checker_id,
                    expire_at=datetime(2026, 1, 1, tzinfo=UTC),
                    last_status=IdleCheckPhase.IDLE,
                    last_message="The session remains idle.",
                )
            )
        return session_id

    @pytest.fixture
    async def terminated_session_with_expired_check(
        self,
        database: ExtendedAsyncSAEngine,
    ) -> SessionId:
        scope = _expired_check_scope_fixture("terminated")
        session_id = SessionId(uuid.uuid4())
        checker_id = IdleCheckerID(uuid.uuid4())
        async with database.begin_session() as db_sess:
            for scope_row in _expired_check_scope_rows(scope):
                db_sess.add(scope_row)
            db_sess.add(_expired_check_session_row(scope, session_id, SessionStatus.TERMINATED))
            db_sess.add(_expired_check_checker_row(checker_id))
            await db_sess.flush()
            db_sess.add(
                SessionIdleCheckRow(
                    session_id=session_id,
                    idle_checker_id=checker_id,
                    expire_at=datetime(2026, 1, 1, tzinfo=UTC),
                    last_status=IdleCheckPhase.IDLE_EXPIRED,
                    last_message="Judged expired.",
                )
            )
        return session_id

    async def test_returns_each_idle_expired_check_regardless_of_deadline(
        self,
        repository: IdleCheckerRepository,
        expired_check_session: ExpiredCheckSessionData,
    ) -> None:
        batch = await repository.fetch_expired_idle_checks([SessionStatus.RUNNING])
        checks_by_key = {(check.session_id, check.checker_id): check for check in batch.checks}

        assert set(checks_by_key) == {
            (expired_check_session.session_id, expired_check_session.first_checker_id),
            (expired_check_session.session_id, expired_check_session.second_checker_id),
        }
        check = checks_by_key[
            (expired_check_session.session_id, expired_check_session.first_checker_id)
        ]
        assert check.expire_at == expired_check_session.first_expire_at
        assert check.last_status == IdleCheckPhase.IDLE_EXPIRED
        assert check.last_message == "Judged expired."
        assert (
            checks_by_key[
                (expired_check_session.session_id, expired_check_session.second_checker_id)
            ].expire_at
            == expired_check_session.second_expire_at
        )

    async def test_excludes_elapsed_deadline_still_marked_idle(
        self,
        repository: IdleCheckerRepository,
        session_with_elapsed_deadline_still_idle: SessionId,
    ) -> None:
        batch = await repository.fetch_expired_idle_checks([SessionStatus.RUNNING])
        check_session_ids = {check.session_id for check in batch.checks}

        assert batch.checks == ()
        assert session_with_elapsed_deadline_still_idle not in check_session_ids

    async def test_excludes_sessions_not_in_target_statuses(
        self,
        repository: IdleCheckerRepository,
        terminated_session_with_expired_check: SessionId,
    ) -> None:
        batch = await repository.fetch_expired_idle_checks([SessionStatus.RUNNING])
        check_session_ids = {check.session_id for check in batch.checks}

        assert batch.checks == ()
        assert terminated_session_with_expired_check not in check_session_ids


@dataclass(frozen=True)
class ExclusionRows:
    assignment_id: IdleCheckerAssignmentID
    checker_id: IdleCheckerID
    active_session_id: SessionId
    idle_expired_session_id: SessionId
    rowless_session_id: SessionId
    batch_session_id: SessionId
    foreign_session_id: SessionId


class TestSessionIdleCheckExclusions:
    @pytest.fixture
    async def database(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                ProjectResourcePolicyRow,
                DomainRow,
                GroupRow,
                ScalingGroupRow,
                SessionRow,
                IdleCheckerRow,
                IdleCheckerBindingRow,
                SessionIdleCheckRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def repository(self, database: ExtendedAsyncSAEngine) -> IdleCheckerRepository:
        return IdleCheckerRepository(DBOpsProvider(database))

    @pytest.fixture
    async def exclusion_rows(
        self,
        database: ExtendedAsyncSAEngine,
    ) -> ExclusionRows:
        scope = _expired_check_scope_fixture("exclusion")
        foreign_scope = _expired_check_scope_fixture("exclusion-foreign")
        assignment_id = IdleCheckerAssignmentID(uuid.uuid4())
        checker_id = IdleCheckerID(uuid.uuid4())
        active_session_id = SessionId(uuid.uuid4())
        idle_expired_session_id = SessionId(uuid.uuid4())
        rowless_session_id = SessionId(uuid.uuid4())
        batch_session_id = SessionId(uuid.uuid4())
        foreign_session_id = SessionId(uuid.uuid4())
        async with database.begin_session() as db_sess:
            for scope_row in _expired_check_scope_rows(scope):
                db_sess.add(scope_row)
            for scope_row in _expired_check_scope_rows(foreign_scope):
                db_sess.add(scope_row)
            for session_id in (active_session_id, idle_expired_session_id, rowless_session_id):
                db_sess.add(_expired_check_session_row(scope, session_id, SessionStatus.RUNNING))
            db_sess.add(
                _expired_check_session_row(
                    scope, batch_session_id, SessionStatus.RUNNING, SessionTypes.BATCH
                )
            )
            db_sess.add(
                _expired_check_session_row(foreign_scope, foreign_session_id, SessionStatus.RUNNING)
            )
            db_sess.add(_expired_check_checker_row(checker_id))
            await db_sess.flush()
            db_sess.add(
                IdleCheckerBindingRow(
                    id=assignment_id,
                    scope_type=ScopeType.DOMAIN.value,
                    scope_id=scope.domain_id,
                    idle_checker_id=checker_id,
                    enabled=True,
                )
            )
            db_sess.add(
                SessionIdleCheckRow(
                    session_id=active_session_id,
                    idle_checker_id=checker_id,
                    expire_at=datetime(2026, 2, 1, tzinfo=UTC),
                    last_status=IdleCheckPhase.ACTIVE,
                    last_message="active judgment",
                )
            )
            db_sess.add(
                SessionIdleCheckRow(
                    session_id=idle_expired_session_id,
                    idle_checker_id=checker_id,
                    expire_at=datetime(2026, 2, 1, tzinfo=UTC),
                    last_status=IdleCheckPhase.IDLE_EXPIRED,
                    last_message="idle expired judgment",
                )
            )
        return ExclusionRows(
            assignment_id=assignment_id,
            checker_id=checker_id,
            active_session_id=active_session_id,
            idle_expired_session_id=idle_expired_session_id,
            rowless_session_id=rowless_session_id,
            batch_session_id=batch_session_id,
            foreign_session_id=foreign_session_id,
        )

    async def test_exclude_marks_existing_and_missing_rows_excluded(
        self,
        database: ExtendedAsyncSAEngine,
        repository: IdleCheckerRepository,
        exclusion_rows: ExclusionRows,
    ) -> None:
        session_ids = (
            exclusion_rows.active_session_id,
            exclusion_rows.idle_expired_session_id,
            exclusion_rows.rowless_session_id,
        )

        await repository.batch_apply_session_idle_check_exclusions(
            SessionIdleCheckExclusionUpdate(
                exclusions=[
                    SessionIdleCheckTarget(
                        assignment_id=exclusion_rows.assignment_id,
                        session_ids=session_ids,
                    )
                ]
            )
        )

        async with database.begin_readonly_session() as db_sess:
            for session_id in session_ids:
                row = await db_sess.get(
                    SessionIdleCheckRow, (session_id, exclusion_rows.checker_id)
                )
                assert row is not None
                assert row.last_status is IdleCheckPhase.EXCLUDED
                assert row.expire_at is None
                assert row.last_message == "Excluded from idle checks."

    async def test_exclude_tolerates_duplicate_targets(
        self,
        database: ExtendedAsyncSAEngine,
        repository: IdleCheckerRepository,
        exclusion_rows: ExclusionRows,
    ) -> None:
        await repository.batch_apply_session_idle_check_exclusions(
            SessionIdleCheckExclusionUpdate(
                exclusions=[
                    SessionIdleCheckTarget(
                        assignment_id=exclusion_rows.assignment_id,
                        session_ids=(
                            exclusion_rows.active_session_id,
                            exclusion_rows.active_session_id,
                        ),
                    )
                ]
            )
        )

        async with database.begin_readonly_session() as db_sess:
            row = await db_sess.get(
                SessionIdleCheckRow,
                (exclusion_rows.active_session_id, exclusion_rows.checker_id),
            )
        assert row is not None
        assert row.last_status is IdleCheckPhase.EXCLUDED

    async def test_excluded_rows_invisible_to_judgment_grace_and_sweep(
        self,
        repository: IdleCheckerRepository,
        exclusion_rows: ExclusionRows,
    ) -> None:
        await repository.batch_apply_session_idle_check_exclusions(
            SessionIdleCheckExclusionUpdate(
                exclusions=[
                    SessionIdleCheckTarget(
                        assignment_id=exclusion_rows.assignment_id,
                        session_ids=(
                            exclusion_rows.active_session_id,
                            exclusion_rows.idle_expired_session_id,
                        ),
                    )
                ]
            )
        )

        judgment_batch = await repository.fetch_judgment_batch([SessionStatus.RUNNING])
        grace_batch = await repository.fetch_initial_grace_period_checks([SessionStatus.RUNNING])
        expired_batch = await repository.fetch_expired_idle_checks([SessionStatus.RUNNING])
        assert judgment_batch.assignments == []
        assert grace_batch.checks == ()
        assert expired_batch.checks == ()

    async def test_excluded_pair_stays_in_desired_and_current(
        self,
        repository: IdleCheckerRepository,
        exclusion_rows: ExclusionRows,
    ) -> None:
        await repository.batch_apply_session_idle_check_exclusions(
            SessionIdleCheckExclusionUpdate(
                exclusions=[
                    SessionIdleCheckTarget(
                        assignment_id=exclusion_rows.assignment_id,
                        session_ids=(exclusion_rows.active_session_id,),
                    )
                ]
            )
        )

        assignments = await repository.fetch_session_idle_check_assignments([SessionStatus.RUNNING])

        pair = SessionIdleCheckPair(exclusion_rows.active_session_id, exclusion_rows.checker_id)
        assert pair in assignments.desired_pairs
        assert pair in assignments.current_pairs

    async def test_include_restores_not_checked(
        self,
        database: ExtendedAsyncSAEngine,
        repository: IdleCheckerRepository,
        exclusion_rows: ExclusionRows,
    ) -> None:
        await repository.batch_apply_session_idle_check_exclusions(
            SessionIdleCheckExclusionUpdate(
                exclusions=[
                    SessionIdleCheckTarget(
                        assignment_id=exclusion_rows.assignment_id,
                        session_ids=(exclusion_rows.active_session_id,),
                    )
                ]
            )
        )

        await repository.batch_apply_session_idle_check_exclusions(
            SessionIdleCheckExclusionUpdate(
                inclusions=[
                    SessionIdleCheckTarget(
                        assignment_id=exclusion_rows.assignment_id,
                        session_ids=(exclusion_rows.active_session_id,),
                    )
                ]
            )
        )

        async with database.begin_readonly_session() as db_sess:
            row = await db_sess.get(
                SessionIdleCheckRow,
                (exclusion_rows.active_session_id, exclusion_rows.checker_id),
            )
        assert row is not None
        assert row.last_status is IdleCheckPhase.NOT_CHECKED
        assert row.expire_at is None
        assert row.last_message == "Not checked yet."

    async def test_include_does_not_touch_non_excluded_rows(
        self,
        database: ExtendedAsyncSAEngine,
        repository: IdleCheckerRepository,
        exclusion_rows: ExclusionRows,
    ) -> None:
        await repository.batch_apply_session_idle_check_exclusions(
            SessionIdleCheckExclusionUpdate(
                inclusions=[
                    SessionIdleCheckTarget(
                        assignment_id=exclusion_rows.assignment_id,
                        session_ids=(exclusion_rows.idle_expired_session_id,),
                    )
                ]
            )
        )

        async with database.begin_readonly_session() as db_sess:
            row = await db_sess.get(
                SessionIdleCheckRow,
                (exclusion_rows.idle_expired_session_id, exclusion_rows.checker_id),
            )
        assert row is not None
        assert row.last_status is IdleCheckPhase.IDLE_EXPIRED
        assert row.last_message == "idle expired judgment"

    async def test_rejects_session_outside_binding_scope_atomically(
        self,
        database: ExtendedAsyncSAEngine,
        repository: IdleCheckerRepository,
        exclusion_rows: ExclusionRows,
    ) -> None:
        with pytest.raises(IdleCheckerExclusionTargetMismatch):
            await repository.batch_apply_session_idle_check_exclusions(
                SessionIdleCheckExclusionUpdate(
                    exclusions=[
                        SessionIdleCheckTarget(
                            assignment_id=exclusion_rows.assignment_id,
                            session_ids=(
                                exclusion_rows.active_session_id,
                                exclusion_rows.foreign_session_id,
                            ),
                        )
                    ]
                )
            )

        async with database.begin_readonly_session() as db_sess:
            valid_row = await db_sess.get(
                SessionIdleCheckRow,
                (exclusion_rows.active_session_id, exclusion_rows.checker_id),
            )
            foreign_row = await db_sess.get(
                SessionIdleCheckRow,
                (exclusion_rows.foreign_session_id, exclusion_rows.checker_id),
            )
        assert valid_row is not None
        assert valid_row.last_status is IdleCheckPhase.ACTIVE
        assert foreign_row is None

    async def test_rejects_session_type_not_targeted_by_checker(
        self,
        repository: IdleCheckerRepository,
        exclusion_rows: ExclusionRows,
    ) -> None:
        with pytest.raises(IdleCheckerExclusionTargetMismatch):
            await repository.batch_apply_session_idle_check_exclusions(
                SessionIdleCheckExclusionUpdate(
                    exclusions=[
                        SessionIdleCheckTarget(
                            assignment_id=exclusion_rows.assignment_id,
                            session_ids=(exclusion_rows.batch_session_id,),
                        )
                    ]
                )
            )

    async def test_exclude_rejects_unknown_assignment(
        self,
        repository: IdleCheckerRepository,
        exclusion_rows: ExclusionRows,
    ) -> None:
        with pytest.raises(IdleCheckerExclusionTargetMismatch):
            await repository.batch_apply_session_idle_check_exclusions(
                SessionIdleCheckExclusionUpdate(
                    exclusions=[
                        SessionIdleCheckTarget(
                            assignment_id=IdleCheckerAssignmentID(uuid.uuid4()),
                            session_ids=(exclusion_rows.active_session_id,),
                        )
                    ]
                )
            )

    async def test_mixed_exclusions_and_inclusions_in_one_call(
        self,
        database: ExtendedAsyncSAEngine,
        repository: IdleCheckerRepository,
        exclusion_rows: ExclusionRows,
    ) -> None:
        await repository.batch_apply_session_idle_check_exclusions(
            SessionIdleCheckExclusionUpdate(
                exclusions=[
                    SessionIdleCheckTarget(
                        assignment_id=exclusion_rows.assignment_id,
                        session_ids=(exclusion_rows.idle_expired_session_id,),
                    )
                ]
            )
        )

        await repository.batch_apply_session_idle_check_exclusions(
            SessionIdleCheckExclusionUpdate(
                exclusions=[
                    SessionIdleCheckTarget(
                        assignment_id=exclusion_rows.assignment_id,
                        session_ids=(exclusion_rows.active_session_id,),
                    )
                ],
                inclusions=[
                    SessionIdleCheckTarget(
                        assignment_id=exclusion_rows.assignment_id,
                        session_ids=(exclusion_rows.idle_expired_session_id,),
                    )
                ],
            )
        )

        async with database.begin_readonly_session() as db_sess:
            excluded_row = await db_sess.get(
                SessionIdleCheckRow,
                (exclusion_rows.active_session_id, exclusion_rows.checker_id),
            )
            included_row = await db_sess.get(
                SessionIdleCheckRow,
                (exclusion_rows.idle_expired_session_id, exclusion_rows.checker_id),
            )
        assert excluded_row is not None
        assert excluded_row.last_status is IdleCheckPhase.EXCLUDED
        assert included_row is not None
        assert included_row.last_status is IdleCheckPhase.NOT_CHECKED

    async def test_include_rejects_unknown_assignment(
        self,
        repository: IdleCheckerRepository,
        exclusion_rows: ExclusionRows,
    ) -> None:
        with pytest.raises(IdleCheckerAssignmentNotFound):
            await repository.batch_apply_session_idle_check_exclusions(
                SessionIdleCheckExclusionUpdate(
                    inclusions=[
                        SessionIdleCheckTarget(
                            assignment_id=IdleCheckerAssignmentID(uuid.uuid4()),
                            session_ids=(exclusion_rows.active_session_id,),
                        )
                    ]
                )
            )
