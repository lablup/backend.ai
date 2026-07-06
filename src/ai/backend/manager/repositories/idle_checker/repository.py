from __future__ import annotations

from collections import defaultdict
from collections.abc import Collection

from ai.backend.common.types import SessionTypes
from ai.backend.manager.data.idle_checker.types import ScopeRef
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.idle_checker.conditions import IdleCheckerBindingConditions
from ai.backend.manager.models.session.conditions import SessionConditions
from ai.backend.manager.repositories.base import BatchQuerier, NoPagination
from ai.backend.manager.repositories.idle_checker.db_source.db_source import IdleCheckerDBSource
from ai.backend.manager.repositories.idle_checker.types import (
    BoundCheckerData,
    IdleCheckBatchData,
    IdleCheckTargetData,
)
from ai.backend.manager.repositories.ops import DBOpsProvider

__all__ = ("IdleCheckerRepository",)


class IdleCheckerRepository:
    """Reads for the idle-check Source."""

    _db_source: IdleCheckerDBSource

    def __init__(self, ops_provider: DBOpsProvider) -> None:
        self._db_source = IdleCheckerDBSource(ops_provider)

    async def fetch_idle_check_batch(
        self, session_statuses: Collection[SessionStatus]
    ) -> IdleCheckBatchData:
        binding_querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[
                IdleCheckerBindingConditions.enabled(),
            ],
        )
        bound_checkers = await self._db_source.fetch_bound_checkers(binding_querier)
        if not bound_checkers:
            return IdleCheckBatchData(targets=())

        seen_candidates = set()
        idle_check_candidates: list[tuple[ScopeRef, Collection[SessionTypes]]] = []
        for bound_checker in bound_checkers:
            target_session_types = bound_checker.checker.spec.target_session_types
            candidate_key = (
                bound_checker.scope.scope_type,
                bound_checker.scope.scope_id,
                target_session_types,
            )
            if candidate_key in seen_candidates:
                continue
            seen_candidates.add(candidate_key)
            idle_check_candidates.append((bound_checker.scope, target_session_types))

        session_querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[
                SessionConditions.by_statuses(session_statuses),
                SessionConditions.by_idle_check_candidates(idle_check_candidates),
            ],
        )
        candidate_sessions = await self._db_source.fetch_candidate_sessions(session_querier)
        checkers_by_scope: defaultdict[ScopeRef, list[BoundCheckerData]] = defaultdict(list)
        for bound_checker in bound_checkers:
            checkers_by_scope[bound_checker.scope].append(bound_checker)

        targets: list[IdleCheckTargetData] = []
        for session_row in candidate_sessions:
            checkers: list[BoundCheckerData] = []
            for scope in session_row.scopes:
                for bound in checkers_by_scope.get(scope, ()):
                    if session_row.session_type in bound.checker.spec.target_session_types:
                        checkers.append(bound)
            if not checkers:
                continue
            targets.append(
                IdleCheckTargetData(
                    session=session_row.session,
                    checkers=tuple(checkers),
                )
            )

        return IdleCheckBatchData(targets=tuple(targets))
