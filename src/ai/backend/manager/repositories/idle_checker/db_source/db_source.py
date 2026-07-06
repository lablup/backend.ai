"""DB reads backing the idle-check Source: the per-session checker batch."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from ai.backend.common.types import SessionId
from ai.backend.manager.data.idle_checker.types import IdleCheckSession, ScopeRef, ScopeType
from ai.backend.manager.models.idle_checker.row import IdleCheckerBindingRow, IdleCheckerRow
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.idle_checker.types import (
    BoundCheckerData,
    IdleCheckerDefinitionData,
    IdleCheckSessionData,
)
from ai.backend.manager.repositories.ops import DBOpsProvider


class IdleCheckerDBSource:
    _ops: DBOpsProvider

    def __init__(self, ops_provider: DBOpsProvider) -> None:
        self._ops = ops_provider

    async def fetch_bound_checkers(
        self,
        querier: BatchQuerier,
    ) -> Sequence[BoundCheckerData]:
        binding_query = sa.select(
            IdleCheckerBindingRow.scope_type,
            IdleCheckerBindingRow.scope_id,
            IdleCheckerBindingRow.created_at,
            IdleCheckerBindingRow.idle_checker_id,
            IdleCheckerRow.checker_type,
            IdleCheckerRow.spec,
        ).join(IdleCheckerRow, IdleCheckerBindingRow.idle_checker_id == IdleCheckerRow.id)

        async with self._ops.read_ops() as r:
            binding_rows = (await r.batch_query_in_global(binding_query, querier)).rows
        bound_checkers: list[BoundCheckerData] = []
        for row in binding_rows:
            scope = ScopeRef(
                scope_type=ScopeType(row.scope_type),
                scope_id=row.scope_id,
            )
            checker = IdleCheckerDefinitionData(
                checker_id=row.idle_checker_id,
                checker_type=row.checker_type,
                spec=row.spec,
            )
            bound_checkers.append(
                BoundCheckerData(
                    scope=scope,
                    binding_created_at=row.created_at,
                    checker=checker,
                )
            )
        return bound_checkers

    async def fetch_candidate_sessions(
        self,
        querier: BatchQuerier,
    ) -> Sequence[IdleCheckSessionData]:
        session_query = sa.select(
            SessionRow.id,
            SessionRow.created_at,
            SessionRow.starts_at,
            SessionRow.session_type,
            SessionRow.resource_group_id,
            SessionRow.group_id,
            SessionRow.domain_id,
        )
        async with self._ops.read_ops() as r:
            session_rows = (await r.batch_query_in_global(session_query, querier)).rows
        return tuple(
            IdleCheckSessionData(
                session=IdleCheckSession(
                    session_id=SessionId(row.id),
                    created_at=row.created_at,
                    starts_at=row.starts_at,
                ),
                session_type=row.session_type,
                scopes=(
                    ScopeRef(ScopeType.RESOURCE_GROUP, row.resource_group_id),
                    ScopeRef(ScopeType.PROJECT, row.group_id),
                    ScopeRef(ScopeType.DOMAIN, row.domain_id),
                ),
            )
            for row in session_rows
        )
