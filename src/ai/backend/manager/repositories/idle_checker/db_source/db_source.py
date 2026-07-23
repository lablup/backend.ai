"""DB reads backing idle-check judgment and expiry-sweep Sources."""

from __future__ import annotations

from collections.abc import Collection, Sequence
from datetime import datetime
from itertools import batched
from typing import cast

import sqlalchemy as sa

from ai.backend.common.data.idle_checker.types import (
    CheckerType,
    IdleCheckerSpec,
    IdleCheckPhase,
)
from ai.backend.common.data.permission.types import ScopeType
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionId, SessionTypes
from ai.backend.manager.data.idle_checker.types import IdleCheckSession
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.idle_checker.row import (
    IdleCheckerBindingRow,
    IdleCheckerRow,
    SessionIdleCheckRow,
)
from ai.backend.manager.models.session.conditions import SessionConditions
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.repositories.base import (
    BatchPurger,
    BatchQuerier,
    BulkCreator,
    NoPagination,
)
from ai.backend.manager.repositories.idle_checker.creators import SessionIdleCheckCreatorSpec
from ai.backend.manager.repositories.idle_checker.purgers import (
    SessionIdleCheckBatchPurgerSpec,
)
from ai.backend.manager.repositories.idle_checker.types import (
    ExpiredIdleCheckBatchData,
    ExpiredIdleCheckData,
    IdleCheckAssignmentData,
    IdleCheckBatchData,
    IdleCheckerDefinitionData,
    InitialGracePeriodBatchData,
    InitialGracePeriodCheckData,
    SessionIdleCheckAssignmentData,
    SessionIdleCheckPair,
)
from ai.backend.manager.repositories.ops import DBOpsProvider

_ASSIGNMENT_DELETE_BATCH_SIZE = 1000


class IdleCheckerDBSource:
    _ops: DBOpsProvider

    def __init__(self, ops_provider: DBOpsProvider) -> None:
        self._ops = ops_provider

    async def fetch_judgment_batch(
        self,
        session_statuses: Collection[SessionStatus],
    ) -> IdleCheckBatchData:
        query = (
            sa.select(
                SessionRow.id.label("session_id"),
                SessionRow.created_at.label("session_created_at"),
                SessionRow.starts_at.label("session_starts_at"),
                IdleCheckerRow.id.label("checker_id"),
                IdleCheckerRow.checker_type,
                IdleCheckerRow.target_session_types,
                IdleCheckerRow.spec,
            )
            .select_from(SessionIdleCheckRow)
            .join(SessionRow, SessionIdleCheckRow.session_id == SessionRow.id)
            .join(IdleCheckerRow, SessionIdleCheckRow.idle_checker_id == IdleCheckerRow.id)
            .where(
                SessionRow.status.in_(session_statuses),
                SessionIdleCheckRow.last_status.in_((IdleCheckPhase.ACTIVE, IdleCheckPhase.IDLE)),
            )
        )
        querier = BatchQuerier(pagination=NoPagination())
        async with self._ops.read_ops() as r:
            rows = (await r.batch_query_in_global(query, querier)).rows
        return IdleCheckBatchData(
            assignments=[
                IdleCheckAssignmentData(
                    session=IdleCheckSession(
                        session_id=SessionId(row.session_id),
                        created_at=row.session_created_at,
                        starts_at=row.session_starts_at,
                    ),
                    checker=IdleCheckerDefinitionData(
                        checker_id=cast(IdleCheckerID, row.checker_id),
                        checker_type=cast(CheckerType, row.checker_type),
                        target_session_types=frozenset(
                            cast(Sequence[SessionTypes], row.target_session_types)
                        ),
                        spec=cast(IdleCheckerSpec, row.spec),
                    ),
                )
                for row in rows
            ]
        )

    async def fetch_expired_idle_checks(
        self,
        session_statuses: Collection[SessionStatus],
    ) -> ExpiredIdleCheckBatchData:
        check_query = (
            sa.select(SessionIdleCheckRow)
            .join(SessionRow, SessionIdleCheckRow.session_id == SessionRow.id)
            .where(SessionIdleCheckRow.last_status == IdleCheckPhase.IDLE_EXPIRED)
        )
        async with self._ops.read_ops() as r:
            now = await r.current_time()
            querier = BatchQuerier(
                pagination=NoPagination(),
                conditions=[
                    SessionConditions.by_statuses(session_statuses),
                ],
            )
            result_rows = (await r.batch_query_in_global(check_query, querier)).rows
        checks: list[ExpiredIdleCheckData] = []
        for row in result_rows:
            check_row: SessionIdleCheckRow = row.SessionIdleCheckRow
            checks.append(
                ExpiredIdleCheckData(
                    session_id=check_row.session_id,
                    checker_id=check_row.idle_checker_id,
                    expire_at=check_row.expire_at,
                    last_status=check_row.last_status,
                    last_message=check_row.last_message,
                )
            )
        return ExpiredIdleCheckBatchData(checks=tuple(checks), now=now)

    async def fetch_initial_grace_period_checks(
        self,
        session_statuses: Collection[SessionStatus],
    ) -> InitialGracePeriodBatchData:
        query = (
            sa.select(
                SessionIdleCheckRow.session_id,
                SessionIdleCheckRow.idle_checker_id,
                SessionIdleCheckRow.updated_at,
                IdleCheckerRow.initial_grace_period_seconds,
            )
            .select_from(SessionIdleCheckRow)
            .join(SessionRow, SessionIdleCheckRow.session_id == SessionRow.id)
            .join(IdleCheckerRow, SessionIdleCheckRow.idle_checker_id == IdleCheckerRow.id)
            .where(
                SessionRow.status.in_(session_statuses),
                SessionIdleCheckRow.last_status == IdleCheckPhase.NOT_CHECKED,
            )
        )
        querier = BatchQuerier(pagination=NoPagination())
        async with self._ops.read_ops() as r:
            now = await r.current_time()
            rows = (await r.batch_query_in_global(query, querier)).rows
        return InitialGracePeriodBatchData(
            checks=tuple(
                InitialGracePeriodCheckData(
                    pair=SessionIdleCheckPair(
                        session_id=SessionId(row.session_id),
                        checker_id=cast(IdleCheckerID, row.idle_checker_id),
                    ),
                    initial_grace_period_seconds=row.initial_grace_period_seconds,
                    grace_started_at=row.updated_at,
                )
                for row in rows
            ),
            now=now,
        )

    async def fetch_session_idle_check_assignments(
        self,
        session_statuses: Collection[SessionStatus],
    ) -> SessionIdleCheckAssignmentData:
        scope_matches = sa.or_(
            sa.and_(
                IdleCheckerBindingRow.scope_type == ScopeType.RESOURCE_GROUP.value,
                IdleCheckerBindingRow.scope_id == SessionRow.resource_group_id,
            ),
            sa.and_(
                IdleCheckerBindingRow.scope_type == ScopeType.PROJECT.value,
                IdleCheckerBindingRow.scope_id == SessionRow.group_id,
            ),
            sa.and_(
                IdleCheckerBindingRow.scope_type == ScopeType.DOMAIN.value,
                IdleCheckerBindingRow.scope_id == SessionRow.domain_id,
            ),
        )
        desired_query = (
            sa.select(
                SessionRow.id,
                IdleCheckerBindingRow.idle_checker_id,
            )
            .select_from(SessionRow)
            .join(IdleCheckerBindingRow, scope_matches)
            .join(
                IdleCheckerRow,
                sa.and_(
                    IdleCheckerRow.id == IdleCheckerBindingRow.idle_checker_id,
                    SessionRow.session_type == sa.any_(IdleCheckerRow.target_session_types),
                ),
            )
            .where(
                SessionRow.status.in_(session_statuses),
                SessionRow.starts_at.is_not(None),
                IdleCheckerBindingRow.enabled == sa.true(),
            )
            .distinct()
        )
        current_query = (
            sa.select(
                SessionIdleCheckRow.session_id,
                SessionIdleCheckRow.idle_checker_id,
            )
            .join(SessionRow, SessionIdleCheckRow.session_id == SessionRow.id)
            .where(SessionRow.status.in_(session_statuses))
        )
        querier = BatchQuerier(pagination=NoPagination())
        async with self._ops.read_ops() as r:
            now = await r.current_time()
            desired_rows = (await r.batch_query_in_global(desired_query, querier)).rows
            current_rows = (await r.batch_query_in_global(current_query, querier)).rows
        return SessionIdleCheckAssignmentData(
            desired_pairs=tuple(
                SessionIdleCheckPair(
                    session_id=SessionId(row.id),
                    checker_id=cast(IdleCheckerID, row.idle_checker_id),
                )
                for row in desired_rows
            ),
            current_pairs=tuple(
                SessionIdleCheckPair(
                    session_id=SessionId(row.session_id),
                    checker_id=cast(IdleCheckerID, row.idle_checker_id),
                )
                for row in current_rows
            ),
            now=now,
        )

    async def sync_session_idle_check_assignments(
        self,
        pairs_to_create: Sequence[SessionIdleCheckPair],
        pairs_to_delete: Sequence[SessionIdleCheckPair],
        now: datetime,
    ) -> None:
        async with self._ops.write_ops() as w:
            if pairs_to_create:
                await w.bulk_create(
                    BulkCreator(
                        specs=[SessionIdleCheckCreatorSpec(pair, now) for pair in pairs_to_create]
                    )
                )
            if pairs_to_delete:
                for pair_batch in batched(pairs_to_delete, _ASSIGNMENT_DELETE_BATCH_SIZE):
                    await w.batch_purge(
                        BatchPurger(
                            spec=SessionIdleCheckBatchPurgerSpec(pair_batch),
                            batch_size=_ASSIGNMENT_DELETE_BATCH_SIZE,
                        )
                    )
