from __future__ import annotations

from collections.abc import Collection, Sequence

from ai.backend.common.data.entity.idle_checker import IdleCheckerAssignmentID, IdleCheckerID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.filter_specs import UUIDEqualMatchSpec
from ai.backend.common.data.idle_checker.types import IdleCheckPhase
from ai.backend.common.data.permission.types import ScopeType
from ai.backend.manager.data.common.types import SearchResult
from ai.backend.manager.data.idle_checker.types import IdleCheckerAssignmentData, IdleJudgmentData
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.errors.idle_checker import IdleCheckerAssignmentNotFound
from ai.backend.manager.models.idle_checker.conditions import IdleCheckerAssignmentConditions
from ai.backend.manager.models.idle_checker.searchers import IdleCheckerAssignmentSearcher
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.repositories.idle_checker.db_source.db_source import IdleCheckerDBSource
from ai.backend.manager.repositories.idle_checker.types import (
    ExpiredIdleCheckBatchData,
    IdleCheckBatchData,
    InitialGracePeriodBatchData,
    SessionIdleCheckAssignmentData,
    SessionIdleCheckBatchResult,
    SessionIdleCheckPair,
)
from ai.backend.manager.repositories.ops import DBOpsProvider
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.relation.provider import RelationOpsProvider

__all__ = ("IdleCheckerRepository",)


class IdleCheckerRepository:
    """The bindings, through the relation ops, and the reconciler's data access,
    through the legacy source. The definition catalog runs against ops."""

    _db_source: IdleCheckerDBSource
    _relation_ops: RelationOpsProvider

    def __init__(
        self,
        ops_provider: DBOpsProvider,
        relation_ops_provider: RelationOpsProvider,
        v2_ops_provider: V2DBOpsProvider,
    ) -> None:
        self._db_source = IdleCheckerDBSource(ops_provider, v2_ops_provider, relation_ops_provider)
        self._relation_ops = relation_ops_provider

    async def get_assignment(
        self, assignment_id: IdleCheckerAssignmentID
    ) -> IdleCheckerAssignmentData:
        async with self._relation_ops.read_ops() as r:
            result = await r.search_in_global(
                IdleCheckerAssignmentSearcher(
                    pagination=OffsetPagination(limit=1),
                    conditions=[IdleCheckerAssignmentConditions.by_id(assignment_id)],
                )
            )
        if not result.items:
            raise IdleCheckerAssignmentNotFound(str(assignment_id))
        return result.items[0]

    async def get_assignment_by_pair(
        self, scope: EntityIdentifier, checker_id: IdleCheckerID
    ) -> IdleCheckerAssignmentData:
        async with self._relation_ops.read_ops() as r:
            result = await r.search_in_global(
                IdleCheckerAssignmentSearcher(
                    pagination=OffsetPagination(limit=1),
                    conditions=[
                        IdleCheckerAssignmentConditions.by_scope_type_equals(
                            ScopeType(scope.entity_type())
                        ),
                        IdleCheckerAssignmentConditions.by_scope_id_equals(
                            UUIDEqualMatchSpec(value=scope, negated=False)
                        ),
                        IdleCheckerAssignmentConditions.by_idle_checker_id_equals(
                            UUIDEqualMatchSpec(value=checker_id, negated=False)
                        ),
                    ],
                )
            )
        if not result.items:
            raise IdleCheckerAssignmentNotFound(f"{scope.entity_type()}:{scope} -> {checker_id}")
        return result.items[0]

    async def admin_search_assignments(
        self, searcher: IdleCheckerAssignmentSearcher
    ) -> SearchResult[IdleCheckerAssignmentData]:
        async with self._relation_ops.read_ops() as r:
            result = await r.search_in_global(searcher)
        return SearchResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def scoped_search_assignments(
        self,
        scopes: Sequence[OperationScope],
        searcher: IdleCheckerAssignmentSearcher,
    ) -> SearchResult[IdleCheckerAssignmentData]:
        """Search bindings whose rows match any of ``scopes`` (OR), narrowed by ``searcher``."""
        async with self._relation_ops.read_ops() as r:
            result = await r.search_with_scopes(scopes, searcher)
        return SearchResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def fetch_judgment_batch(
        self, session_statuses: Collection[SessionStatus]
    ) -> IdleCheckBatchData:
        return await self._db_source.fetch_judgment_batch(session_statuses)

    async def fetch_session_idle_check_assignments(
        self,
        session_statuses: Collection[SessionStatus],
    ) -> SessionIdleCheckAssignmentData:
        return await self._db_source.fetch_session_idle_check_assignments(session_statuses)

    async def fetch_initial_grace_period_checks(
        self,
        session_statuses: Collection[SessionStatus],
    ) -> InitialGracePeriodBatchData:
        return await self._db_source.fetch_initial_grace_period_checks(session_statuses)

    async def fetch_expired_idle_checks(
        self, session_statuses: Collection[SessionStatus]
    ) -> ExpiredIdleCheckBatchData:
        return await self._db_source.fetch_expired_idle_checks(session_statuses)

    async def sync_session_idle_check_assignments(
        self,
        pairs_to_create: Sequence[SessionIdleCheckPair],
        pairs_to_delete: Sequence[SessionIdleCheckPair],
    ) -> None:
        await self._db_source.sync_session_idle_check_assignments(
            pairs_to_create,
            pairs_to_delete,
        )

    async def batch_update_session_idle_check_phase(
        self,
        pairs: Sequence[SessionIdleCheckPair],
        *,
        from_phase: IdleCheckPhase,
        to_phase: IdleCheckPhase,
    ) -> None:
        await self._db_source.batch_update_session_idle_check_phase(
            pairs,
            from_phase=from_phase,
            to_phase=to_phase,
        )

    async def batch_exclude_session_idle_checks(
        self,
        pairs: Sequence[SessionIdleCheckPair],
        user_id: UserID,
    ) -> SessionIdleCheckBatchResult:
        return await self._db_source.batch_exclude_session_idle_checks(pairs, user_id)

    async def batch_include_session_idle_checks(
        self,
        pairs: Sequence[SessionIdleCheckPair],
        user_id: UserID,
    ) -> SessionIdleCheckBatchResult:
        return await self._db_source.batch_include_session_idle_checks(pairs, user_id)

    async def batch_apply_session_idle_check_judgments(
        self,
        judgments: Sequence[IdleJudgmentData],
    ) -> None:
        await self._db_source.batch_apply_session_idle_check_judgments(judgments)
