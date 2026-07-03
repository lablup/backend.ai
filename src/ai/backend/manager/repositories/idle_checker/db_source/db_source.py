"""DB reads backing the idle-check Source: the per-session checker batch."""

from __future__ import annotations

from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.common.types import SessionId, SessionTypes
from ai.backend.manager.data.idle_checker.types import IdleCheckSession, ScopeRef, ScopeType
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.idle_checker.row import IdleCheckerBindingRow, IdleCheckerRow
from ai.backend.manager.models.scaling_group.row import ScalingGroupRow
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
        self, session_statuses: Collection[SessionStatus]
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
        session_query = (
            sa.select(
                SessionRow.id.label("session_id"),
                SessionRow.created_at.label("session_created_at"),
                SessionRow.starts_at.label("session_starts_at"),
                ScalingGroupRow.id.label("resource_group_id"),
                SessionRow.group_id.label("project_id"),
                DomainRow.id.label("domain_id"),
            )
            .select_from(SessionRow)
            .join(DomainRow, SessionRow.domain_name == DomainRow.name)
            .join(ScalingGroupRow, SessionRow.scaling_group_name == ScalingGroupRow.name)
            .where(
                sa.and_(
                    # The caller (idle-check stage) owns which statuses are idle-check targets;
                    # today that is RUNNING only. Kept as a parameter so the policy stays in the
                    # stage's target_statuses rather than baked into this read.
                    SessionRow.status.in_(session_statuses),
                    SessionRow.session_type != SessionTypes.INFERENCE,
                    self._enabled_binding_exists_query(),
                )
            )
            .order_by(SessionRow.created_at, SessionRow.id)
        )

        querier = BatchQuerier(pagination=NoPagination())
        async with self._ops.read_ops() as r:
            binding_rows = (await r.batch_query_in_global(binding_query, querier)).rows
            if not binding_rows:
                return IdleCheckBatchData(targets=())
            session_rows = (await r.batch_query_in_global(session_query, querier)).rows

        checkers_by_scope: dict[ScopeRef, list[BoundCheckerData]] = {}
        for binding_row in binding_rows:
            binding_scope = ScopeRef(ScopeType(binding_row.scope_type), binding_row.scope_id)
            checker = IdleCheckerDefinitionData(
                checker_id=binding_row.checker_id,
                checker_type=binding_row.checker_type,
                spec=binding_row.spec,
            )
            checkers_by_scope.setdefault(binding_scope, []).append(
                BoundCheckerData(
                    scope=binding_scope,
                    binding_created_at=binding_row.binding_created_at,
                    checker=checker,
                )
            )

        targets: list[IdleCheckTargetData] = []
        for session_row in session_rows:
            scopes = (
                ScopeRef(ScopeType.RESOURCE_GROUP, session_row.resource_group_id),
                ScopeRef(ScopeType.PROJECT, session_row.project_id),
                ScopeRef(ScopeType.DOMAIN, session_row.domain_id),
            )
            checkers = tuple(
                checker for scope in scopes for checker in checkers_by_scope.get(scope, ())
            )
            targets.append(
                IdleCheckTargetData(
                    session=IdleCheckSession(
                        session_id=SessionId(session_row.session_id),
                        created_at=session_row.session_created_at,
                        starts_at=session_row.session_starts_at,
                    ),
                    checkers=checkers,
                )
            )

        return IdleCheckBatchData(targets=tuple(targets))

    def _enabled_binding_exists_query(self) -> sa.sql.elements.ColumnElement[bool]:
        return sa.exists().where(
            sa.and_(
                IdleCheckerBindingRow.enabled == sa.true(),
                sa.or_(
                    sa.and_(
                        IdleCheckerBindingRow.scope_type == ScopeType.RESOURCE_GROUP.value,
                        IdleCheckerBindingRow.scope_id == ScalingGroupRow.id,
                    ),
                    sa.and_(
                        IdleCheckerBindingRow.scope_type == ScopeType.PROJECT.value,
                        IdleCheckerBindingRow.scope_id == SessionRow.group_id,
                    ),
                    sa.and_(
                        IdleCheckerBindingRow.scope_type == ScopeType.DOMAIN.value,
                        IdleCheckerBindingRow.scope_id == DomainRow.id,
                    ),
                ),
            )
        )
