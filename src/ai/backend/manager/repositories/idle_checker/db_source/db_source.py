"""DB reads backing idle-check judgment and expiry-sweep Sources."""

from __future__ import annotations

from collections.abc import Collection, Sequence
from datetime import datetime
from itertools import batched
from typing import cast

import sqlalchemy as sa

from ai.backend.common.data.entity.idle_checker import IdleCheckerID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.idle_checker.types import (
    CheckerType,
    IdleCheckerSpec,
    IdleCheckPhase,
)
from ai.backend.common.data.permission.types import ScopeType
from ai.backend.common.types import SessionId, SessionTypes
from ai.backend.manager.data.idle_checker.types import IdleCheckSession, IdleJudgmentData
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.idle_checker.creators import SessionIdleCheckLink
from ai.backend.manager.models.idle_checker.purgers import SessionIdleCheckUnlink
from ai.backend.manager.models.idle_checker.row import (
    IdleCheckerBindingRow,
    IdleCheckerRow,
    SessionIdleCheckRow,
)
from ai.backend.manager.models.idle_checker.updaters import (
    SessionIdleCheckJudgmentBatchUpdater,
    SessionIdleCheckPhaseBatchUpdater,
)
from ai.backend.manager.models.idle_checker.upserters import (
    SessionIdleCheckExcluder,
    SessionIdleCheckIncluder,
)
from ai.backend.manager.models.session.conditions import SessionConditions
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.repositories.base import (
    BatchQuerier,
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
    SessionIdleCheckBatchResult,
    SessionIdleCheckPair,
    SessionIdleCheckPairResult,
)
from ai.backend.manager.repositories.ops import DBOpsProvider
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.relation.provider import RelationOpsProvider

_ASSIGNMENT_DELETE_BATCH_SIZE = 1000


_IDLE_CHECK_UPDATE_BATCH_SIZE = 1000


class IdleCheckerDBSource:
    _ops: DBOpsProvider
    _v2_ops: V2DBOpsProvider
    _relation_ops: RelationOpsProvider

    def __init__(
        self,
        ops_provider: DBOpsProvider,
        v2_ops_provider: V2DBOpsProvider,
        relation_ops_provider: RelationOpsProvider,
    ) -> None:
        self._ops = ops_provider
        self._v2_ops = v2_ops_provider
        self._relation_ops = relation_ops_provider

    async def fetch_judgment_batch(
        self,
        session_statuses: Collection[SessionStatus],
    ) -> IdleCheckBatchData:
        query = (
            sa.select(
                SessionRow.id.label("session_id"),
                SessionRow.created_at.label("session_created_at"),
                SessionRow.starts_at.label("session_starts_at"),
                SessionIdleCheckRow.expire_at.label("session_expire_at"),
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
                SessionIdleCheckRow.last_status.in_((
                    IdleCheckPhase.READY_TO_CHECK,
                    IdleCheckPhase.ACTIVE,
                    IdleCheckPhase.IDLE,
                )),
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
                        expire_at=row.session_expire_at,
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
            .where(
                SessionIdleCheckRow.last_status == IdleCheckPhase.IDLE_EXPIRED,
                SessionIdleCheckRow.expire_at.is_not(None),
            )
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
                    expire_at=cast(datetime, check_row.expire_at),
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
            sa.and_(
                IdleCheckerBindingRow.scope_type == ScopeType.USER.value,
                IdleCheckerBindingRow.scope_id == SessionRow.user_uuid,
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
    ) -> None:
        async with self._relation_ops.write_ops() as w:
            if pairs_to_create:
                await w.create_relations(
                    SessionIdleCheckLink(),
                    [(SessionID(pair.session_id), pair.checker_id) for pair in pairs_to_create],
                )
            for pair_batch in batched(pairs_to_delete, _ASSIGNMENT_DELETE_BATCH_SIZE):
                await w.purge_relations(
                    SessionIdleCheckUnlink(),
                    [(SessionID(pair.session_id), pair.checker_id) for pair in pair_batch],
                )

    async def batch_update_session_idle_check_phase(
        self,
        pairs: Sequence[SessionIdleCheckPair],
        *,
        from_phase: IdleCheckPhase,
        to_phase: IdleCheckPhase,
    ) -> None:
        async with self._v2_ops.write_ops() as w:
            for pair_batch in batched(pairs, _IDLE_CHECK_UPDATE_BATCH_SIZE):
                await w.batch_update_in_global(
                    SessionIdleCheckPhaseBatchUpdater(
                        pairs=[(pair.session_id, pair.checker_id) for pair in pair_batch],
                        from_phase=from_phase,
                        to_phase=to_phase,
                    )
                )

    async def batch_exclude_session_idle_checks(
        self,
        pairs: Sequence[SessionIdleCheckPair],
        user_id: UserID,
    ) -> SessionIdleCheckBatchResult:
        """Exclude each named pair, one savepoint per pair, answering how each fared
        in the order named.

        An upsert: a pair the checker has not reached yet is written excluded, so the
        exclusion is not lost when the sweep later links it.
        """
        async with self._relation_ops.write_ops() as w:
            result = await w.partial_upsert_relations(
                SessionIdleCheckExcluder(user_id=user_id),
                [(SessionID(pair.session_id), pair.checker_id) for pair in pairs],
            )
        return SessionIdleCheckBatchResult(
            results=[
                SessionIdleCheckPairResult(pair=pair, applied=item.written, error=item.error)
                for pair, item in zip(pairs, result.results, strict=True)
            ]
        )

    async def batch_include_session_idle_checks(
        self,
        pairs: Sequence[SessionIdleCheckPair],
        user_id: UserID,
    ) -> SessionIdleCheckBatchResult:
        """Put each named pair back under its checker, one savepoint per pair,
        answering how each fared in the order named."""
        async with self._relation_ops.write_ops() as w:
            result = await w.partial_upsert_relations(
                SessionIdleCheckIncluder(user_id=user_id),
                [(SessionID(pair.session_id), pair.checker_id) for pair in pairs],
            )
        return SessionIdleCheckBatchResult(
            results=[
                SessionIdleCheckPairResult(pair=pair, applied=item.written, error=item.error)
                for pair, item in zip(pairs, result.results, strict=True)
            ]
        )

    async def batch_apply_session_idle_check_judgments(
        self,
        judgments: Sequence[IdleJudgmentData],
    ) -> None:
        if not judgments:
            return
        async with self._v2_ops.write_ops() as w:
            await w.batch_update_in_global(
                SessionIdleCheckJudgmentBatchUpdater(judgments=judgments)
            )
