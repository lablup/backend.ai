"""DB reads backing the idle-check Source: the per-session checker batch."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.common.types import SessionId
from ai.backend.manager.data.idle_checker.types import IdleCheckSession, ScopeRef, ScopeType
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.idle_checker.row import IdleCheckerBindingRow, IdleCheckerRow
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.repositories.base import BatchQuerier, NoPagination
from ai.backend.manager.repositories.idle_checker.types import (
    BoundCheckerData,
    IdleCheckBatchData,
    IdleCheckerDefinitionData,
    IdleCheckTargetData,
)
from ai.backend.manager.repositories.ops import DBOpsProvider


class IdleCheckerDBSource:
    _ops: DBOpsProvider

    def __init__(self, ops_provider: DBOpsProvider) -> None:
        self._ops = ops_provider

    async def fetch_idle_check_batch(
        self,
        session_statuses: Collection[SessionStatus],
    ) -> IdleCheckBatchData:
        """Fetch sessions with the scope-bound idle checkers applicable to each session."""
        binding_query = (
            sa.select(
                IdleCheckerBindingRow.scope_type,
                IdleCheckerBindingRow.scope_id,
                IdleCheckerBindingRow.created_at.label("binding_created_at"),
                IdleCheckerBindingRow.idle_checker_id,
                IdleCheckerRow.id.label("checker_id"),
                IdleCheckerRow.checker_type,
                IdleCheckerRow.spec,  # typed: PydanticColumn loads it to an IdleCheckerSpec
            )
            .join(IdleCheckerRow, IdleCheckerBindingRow.idle_checker_id == IdleCheckerRow.id)
            .where(IdleCheckerBindingRow.enabled == sa.true())
            .order_by(
                IdleCheckerBindingRow.scope_type,
                IdleCheckerBindingRow.scope_id,
                IdleCheckerBindingRow.created_at,
                IdleCheckerBindingRow.idle_checker_id,
            )
        )

        querier = BatchQuerier(pagination=NoPagination())
        async with self._ops.read_ops() as r:
            binding_rows = (await r.batch_query_in_global(binding_query, querier)).rows
            if not binding_rows:
                return IdleCheckBatchData(targets=())

            scope_columns = {
                ScopeType.RESOURCE_GROUP: SessionRow.resource_group_id,
                ScopeType.PROJECT: SessionRow.group_id,
                ScopeType.DOMAIN: SessionRow.domain_id,
            }
            checkers_by_scope: defaultdict[ScopeRef, list[BoundCheckerData]] = defaultdict(list)
            # A scope can host several checkers, so bindings often yield the same candidate
            # term; dedupe by (scope, target types) while still attaching every checker.
            candidate_conditions = []
            seen_candidates = set()
            for binding_row in binding_rows:
                scope_type = ScopeType(binding_row.scope_type)
                scope = ScopeRef(scope_type, binding_row.scope_id)
                checker = IdleCheckerDefinitionData(
                    checker_id=binding_row.checker_id,
                    checker_type=binding_row.checker_type,
                    spec=binding_row.spec,
                )
                checkers_by_scope[scope].append(
                    BoundCheckerData(
                        scope=scope,
                        binding_created_at=binding_row.binding_created_at,
                        checker=checker,
                    )
                )
                candidate_key = (
                    scope_type,
                    binding_row.scope_id,
                    checker.spec.target_session_types,
                )
                if candidate_key in seen_candidates:
                    continue
                seen_candidates.add(candidate_key)
                candidate_conditions.append(
                    sa.and_(
                        scope_columns[scope_type] == binding_row.scope_id,
                        SessionRow.session_type.in_(checker.spec.target_session_types),
                    )
                )

            session_query = (
                sa.select(
                    SessionRow.id,
                    SessionRow.created_at,
                    SessionRow.starts_at,
                    SessionRow.session_type,
                    SessionRow.resource_group_id,
                    SessionRow.group_id,
                    SessionRow.domain_id,
                )
                .where(
                    sa.and_(
                        SessionRow.status.in_(session_statuses),
                        sa.or_(*candidate_conditions),
                    )
                )
                .order_by(SessionRow.created_at, SessionRow.id)
            )
            session_rows = (await r.batch_query_in_global(session_query, querier)).rows

        targets: list[IdleCheckTargetData] = []
        for session_row in session_rows:
            scopes = (
                ScopeRef(ScopeType.RESOURCE_GROUP, session_row.resource_group_id),
                ScopeRef(ScopeType.PROJECT, session_row.group_id),
                ScopeRef(ScopeType.DOMAIN, session_row.domain_id),
            )
            # Attach only checkers whose target types include this session's type.
            checkers: list[BoundCheckerData] = []
            for scope in scopes:
                for bound in checkers_by_scope.get(scope, ()):
                    if session_row.session_type in bound.checker.spec.target_session_types:
                        checkers.append(bound)
            if not checkers:
                continue
            targets.append(
                IdleCheckTargetData(
                    session=IdleCheckSession(
                        session_id=SessionId(session_row.id),
                        created_at=session_row.created_at,
                        starts_at=session_row.starts_at,
                    ),
                    checkers=tuple(checkers),
                )
            )

        return IdleCheckBatchData(targets=tuple(targets))
