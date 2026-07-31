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
from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.idle_checker import IdleCheckerAssignmentID, IdleCheckerID
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import SessionId, SessionTypes
from ai.backend.manager.data.common.types import SearchResult
from ai.backend.manager.data.idle_checker.types import (
    IdleCheckerAssignmentData,
    IdleCheckerData,
    IdleCheckSession,
)
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.errors.idle_checker import (
    IdleCheckerAssignmentNotFound,
    IdleCheckerAssignmentScopeNotFound,
    IdleCheckerExclusionTargetMismatch,
    IdleCheckerNotFound,
)
from ai.backend.manager.models.domain.conditions import DomainConditions
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.models.idle_checker.conditions import SessionIdleCheckConditions
from ai.backend.manager.models.idle_checker.row import (
    IdleCheckerBindingRow,
    IdleCheckerRow,
    SessionIdleCheckRow,
)
from ai.backend.manager.models.scaling_group.conditions import ScalingGroupConditions
from ai.backend.manager.models.scaling_group.row import ScalingGroupRow
from ai.backend.manager.models.scopes import SearchScope
from ai.backend.manager.models.session.conditions import SessionConditions
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.repositories.base import (
    BatchPurger,
    BatchQuerier,
    BatchUpdater,
    BulkCreator,
    BulkUpserter,
    Creator,
    NoPagination,
    OffsetPagination,
    Purger,
    Querier,
    Updater,
)
from ai.backend.manager.repositories.base.rbac.entity_creator import RBACEntityCreator
from ai.backend.manager.repositories.base.rbac.entity_purger import RBACEntityPurger
from ai.backend.manager.repositories.idle_checker.creators import (
    IdleCheckerAssignmentCreatorSpec,
    SessionIdleCheckCreatorSpec,
)
from ai.backend.manager.repositories.idle_checker.purgers import (
    SessionIdleCheckBatchPurgerSpec,
)
from ai.backend.manager.repositories.idle_checker.types import (
    ExpiredIdleCheckBatchData,
    ExpiredIdleCheckData,
    IdleCheckAssignmentData,
    IdleCheckBatchData,
    IdleCheckerDefinitionData,
    IdleJudgmentData,
    InitialGracePeriodBatchData,
    InitialGracePeriodCheckData,
    SessionIdleCheckAssignmentData,
    SessionIdleCheckExclusionUpdate,
    SessionIdleCheckPair,
    SessionIdleCheckTarget,
)
from ai.backend.manager.repositories.idle_checker.updaters import (
    SessionIdleCheckJudgmentBatchUpdaterSpec,
    SessionIdleCheckPhaseBatchUpdaterSpec,
)
from ai.backend.manager.repositories.idle_checker.upserters import (
    SessionIdleCheckExclusionUpserterSpec,
)
from ai.backend.manager.repositories.ops import DBOpsProvider, WriteOps

_ASSIGNMENT_DELETE_BATCH_SIZE = 1000
_IDLE_CHECK_UPDATE_BATCH_SIZE = 1000


class IdleCheckerDBSource:
    _ops: DBOpsProvider

    def __init__(self, ops_provider: DBOpsProvider) -> None:
        self._ops = ops_provider

    async def create(self, creator: Creator[IdleCheckerRow]) -> IdleCheckerData:
        async with self._ops.write_ops() as w:
            checker = (await w.create(creator)).row
            return checker.to_data()

    async def update(self, updater: Updater[IdleCheckerRow]) -> IdleCheckerData:
        async with self._ops.write_ops() as w:
            result = await w.update(updater)
            if result is None:
                raise IdleCheckerNotFound(str(updater.pk_value))
            return result.row.to_data()

    async def purge(self, purger: Purger[IdleCheckerRow]) -> IdleCheckerData:
        async with self._ops.write_ops() as w:
            result = await w.purge(purger)
            if result is None:
                raise IdleCheckerNotFound(str(purger.spec.pk_value()))
            return result.row.to_data()

    async def admin_search(self, querier: BatchQuerier) -> SearchResult[IdleCheckerData]:
        async with self._ops.read_ops() as r:
            result = await r.batch_query_in_global(sa.select(IdleCheckerRow), querier)
        return SearchResult(
            items=[row.IdleCheckerRow.to_data() for row in result.rows],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def create_assignment(
        self, spec: IdleCheckerAssignmentCreatorSpec
    ) -> IdleCheckerAssignmentData:
        async with self._ops.write_ops() as w:
            # Validate on the write path that the referenced scope row exists (BEP-1054).
            match spec.scope_type:
                case ScopeType.DOMAIN:
                    querier = BatchQuerier(
                        pagination=OffsetPagination(limit=1),
                        conditions=[DomainConditions.by_ids([DomainID(spec.scope_id)])],
                    )
                    result = await w.batch_query_in_global(sa.select(DomainRow), querier)
                    scope_exists = bool(result.rows)
                case ScopeType.PROJECT:
                    row = await w.query(Querier(row_class=GroupRow, pk_value=spec.scope_id))
                    scope_exists = row is not None
                case ScopeType.RESOURCE_GROUP:
                    querier = BatchQuerier(
                        pagination=OffsetPagination(limit=1),
                        conditions=[
                            ScalingGroupConditions.by_ids([ResourceGroupID(spec.scope_id)])
                        ],
                    )
                    result = await w.batch_query_in_global(sa.select(ScalingGroupRow), querier)
                    scope_exists = bool(result.rows)
                case _:
                    scope_exists = False
            if not scope_exists:
                raise IdleCheckerAssignmentScopeNotFound(f"{spec.scope_type.value}:{spec.scope_id}")
            creator = RBACEntityCreator(
                spec=spec,
                element_type=RBACElementType.IDLE_CHECKER_ASSIGNMENT,
                scope_ref=RBACElementRef(
                    element_type=RBACElementType(spec.scope_type.value),
                    element_id=str(spec.scope_id),
                ),
            )
            binding = (await w.create_rbac_entity(creator)).row
            return binding.to_data()

    async def update_assignment(
        self, updater: Updater[IdleCheckerBindingRow]
    ) -> IdleCheckerAssignmentData:
        async with self._ops.write_ops() as w:
            result = await w.update(updater)
            if result is None:
                raise IdleCheckerAssignmentNotFound(str(updater.pk_value))
            return result.row.to_data()

    async def purge_assignment(
        self, purger: RBACEntityPurger[IdleCheckerBindingRow]
    ) -> IdleCheckerAssignmentData:
        async with self._ops.write_ops() as w:
            result = await w.purge_rbac_entity(purger)
            if result is None:
                raise IdleCheckerAssignmentNotFound(str(purger.spec.pk_value()))
            return result.row.to_data()

    async def admin_search_assignments(
        self, querier: BatchQuerier
    ) -> SearchResult[IdleCheckerAssignmentData]:
        async with self._ops.read_ops() as r:
            result = await r.batch_query_in_global(sa.select(IdleCheckerBindingRow), querier)
        return SearchResult(
            items=[row.IdleCheckerBindingRow.to_data() for row in result.rows],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def scoped_search_assignments(
        self,
        querier: BatchQuerier,
        scopes: Sequence[SearchScope],
    ) -> SearchResult[IdleCheckerAssignmentData]:
        """Search bindings whose rows match any of ``scopes`` (OR), narrowed by ``querier``."""
        async with self._ops.read_ops() as r:
            result = await r.batch_query_with_scopes(
                sa.select(IdleCheckerBindingRow), querier, scopes
            )
        return SearchResult(
            items=[row.IdleCheckerBindingRow.to_data() for row in result.rows],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

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

    def _binding_covers_session(self) -> sa.ColumnElement[bool]:
        """Join clause matching a binding to the sessions inside its scope."""
        return sa.or_(
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

    async def fetch_session_idle_check_assignments(
        self,
        session_statuses: Collection[SessionStatus],
    ) -> SessionIdleCheckAssignmentData:
        desired_query = (
            sa.select(
                SessionRow.id,
                IdleCheckerBindingRow.idle_checker_id,
            )
            .select_from(SessionRow)
            .join(IdleCheckerBindingRow, self._binding_covers_session())
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
        async with self._ops.write_ops() as w:
            if pairs_to_create:
                await w.bulk_create(
                    BulkCreator(
                        specs=[SessionIdleCheckCreatorSpec(pair) for pair in pairs_to_create]
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

    async def batch_apply_session_idle_check_exclusions(
        self,
        update: SessionIdleCheckExclusionUpdate,
    ) -> None:
        """Apply exclusions and inclusions in a single transaction."""
        async with self._ops.write_ops() as w:
            await self._exclude_session_idle_checks(w, update.exclusions)
            await self._include_session_idle_checks(w, update.inclusions)

    async def _exclude_session_idle_checks(
        self,
        w: WriteOps,
        items: Sequence[SessionIdleCheckTarget],
    ) -> None:
        """Mark each (session, checker) pair EXCLUDED, creating missing rows.

        Every session must be covered by its assignment (existing binding, scope
        match, target session type); any mismatch rejects the whole request.
        """
        if not items:
            return
        assignment_ids = {item.assignment_id for item in items}
        session_ids: set[SessionId] = set()
        for item in items:
            session_ids.update(item.session_ids)
        covered_query = (
            sa.select(
                IdleCheckerBindingRow.id.label("assignment_id"),
                IdleCheckerBindingRow.idle_checker_id,
                SessionRow.id.label("session_id"),
            )
            .select_from(IdleCheckerBindingRow)
            .join(SessionRow, self._binding_covers_session())
            .join(
                IdleCheckerRow,
                sa.and_(
                    IdleCheckerRow.id == IdleCheckerBindingRow.idle_checker_id,
                    SessionRow.session_type == sa.any_(IdleCheckerRow.target_session_types),
                ),
            )
            .where(
                IdleCheckerBindingRow.id.in_(assignment_ids),
                SessionRow.id.in_(session_ids),
            )
        )
        querier = BatchQuerier(pagination=NoPagination())
        covered_rows = (await w.batch_query_in_global(covered_query, querier)).rows
        checker_by_assignment: dict[IdleCheckerAssignmentID, IdleCheckerID] = {}
        covered_pairs: set[tuple[IdleCheckerAssignmentID, SessionId]] = set()
        for row in covered_rows:
            assignment_id = IdleCheckerAssignmentID(row.assignment_id)
            checker_by_assignment[assignment_id] = cast(IdleCheckerID, row.idle_checker_id)
            covered_pairs.add((assignment_id, SessionId(row.session_id)))
        mismatched_refs: list[str] = []
        for item in items:
            for session_id in item.session_ids:
                if (item.assignment_id, session_id) not in covered_pairs:
                    mismatched_refs.append(f"{item.assignment_id}:{session_id}")
        if mismatched_refs:
            raise IdleCheckerExclusionTargetMismatch(", ".join(mismatched_refs))

        pairs: list[SessionIdleCheckPair] = []
        for item in items:
            checker_id = checker_by_assignment[item.assignment_id]
            for session_id in item.session_ids:
                pairs.append(SessionIdleCheckPair(session_id=session_id, checker_id=checker_id))
        # ON CONFLICT cannot touch the same row twice within one statement.
        deduped_pairs = list(dict.fromkeys(pairs))
        for pair_batch in batched(deduped_pairs, _IDLE_CHECK_UPDATE_BATCH_SIZE):
            await w.bulk_upsert(
                BulkUpserter(
                    specs=[SessionIdleCheckExclusionUpserterSpec(pair) for pair in pair_batch]
                ),
                index_elements=["session_id", "idle_checker_id"],
            )

    async def _include_session_idle_checks(
        self,
        w: WriteOps,
        items: Sequence[SessionIdleCheckTarget],
    ) -> None:
        """Move EXCLUDED (session, checker) pairs back to NOT_CHECKED (grace restarts).

        The conditional update is the safety: pairs that do not exist or are not
        EXCLUDED are no-ops, so no coverage validation is needed for this undo.
        """
        if not items:
            return
        assignment_ids = {item.assignment_id for item in items}
        binding_query = sa.select(IdleCheckerBindingRow).where(
            IdleCheckerBindingRow.id.in_(assignment_ids)
        )
        querier = BatchQuerier(pagination=NoPagination())
        binding_rows = (await w.batch_query_in_global(binding_query, querier)).rows
        checker_by_assignment: dict[IdleCheckerAssignmentID, IdleCheckerID] = {}
        for row in binding_rows:
            binding: IdleCheckerBindingRow = row.IdleCheckerBindingRow
            checker_by_assignment[IdleCheckerAssignmentID(binding.id)] = binding.idle_checker_id

        pairs: list[SessionIdleCheckPair] = []
        for item in items:
            checker_id = checker_by_assignment.get(item.assignment_id)
            if checker_id is None:
                continue
            for session_id in item.session_ids:
                pairs.append(SessionIdleCheckPair(session_id=session_id, checker_id=checker_id))

        for pair_batch in batched(pairs, _IDLE_CHECK_UPDATE_BATCH_SIZE):
            pair_values = [(pair.session_id, pair.checker_id) for pair in pair_batch]
            await w.batch_update(
                BatchUpdater(
                    spec=SessionIdleCheckPhaseBatchUpdaterSpec(
                        to_phase=IdleCheckPhase.NOT_CHECKED,
                        message="Not checked yet.",
                    ),
                    conditions=[
                        SessionIdleCheckConditions.by_pairs(pair_values),
                        SessionIdleCheckConditions.by_status_equals(IdleCheckPhase.EXCLUDED),
                    ],
                )
            )

    async def batch_update_session_idle_check_phase(
        self,
        pairs: Sequence[SessionIdleCheckPair],
        *,
        from_phase: IdleCheckPhase,
        to_phase: IdleCheckPhase,
    ) -> None:
        async with self._ops.write_ops() as w:
            for pair_batch in batched(pairs, _IDLE_CHECK_UPDATE_BATCH_SIZE):
                pair_values = [(pair.session_id, pair.checker_id) for pair in pair_batch]
                await w.batch_update(
                    BatchUpdater(
                        spec=SessionIdleCheckPhaseBatchUpdaterSpec(to_phase=to_phase),
                        conditions=[
                            SessionIdleCheckConditions.by_pairs(pair_values),
                            SessionIdleCheckConditions.by_status_equals(from_phase),
                        ],
                    )
                )

    async def batch_apply_session_idle_check_judgments(
        self,
        judgments: Sequence[IdleJudgmentData],
    ) -> None:
        pairs = [(judgment.session_id, judgment.checker_id) for judgment in judgments]
        async with self._ops.write_ops() as w:
            if pairs:
                await w.batch_update(
                    BatchUpdater(
                        spec=SessionIdleCheckJudgmentBatchUpdaterSpec(judgments),
                        conditions=[
                            SessionIdleCheckConditions.by_pairs(pairs),
                            SessionIdleCheckConditions.by_status_not_equals(
                                IdleCheckPhase.IDLE_EXPIRED
                            ),
                        ],
                    )
                )
