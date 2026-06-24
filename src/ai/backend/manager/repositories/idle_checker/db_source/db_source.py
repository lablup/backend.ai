"""DB reads backing the idle-check Source: the normalized scope snapshot."""

from __future__ import annotations

from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionId, SessionTypes
from ai.backend.manager.data.idle_checker.types import IdleCheckSessionView, ScopeRef, ScopeType
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.idle_checker.row import IdleCheckerBindingRow, IdleCheckerRow
from ai.backend.manager.models.scaling_group.row import ScalingGroupRow
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.idle_checker.types import (
    IdleCheckerBindingRef,
    IdleCheckerRef,
    IdleCheckSnapshot,
)


class IdleCheckerDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def fetch_idle_check_snapshot(
        self, session_statuses: Collection[SessionStatus]
    ) -> IdleCheckSnapshot:
        """Fetch sessions and scope-bound idle checkers without expanding to session-checker rows."""
        binding_query = (
            sa.select(
                IdleCheckerBindingRow.scope_type,
                IdleCheckerBindingRow.scope_id,
                IdleCheckerBindingRow.created_at.label("binding_created_at"),
                IdleCheckerBindingRow.idle_checker_id,
                IdleCheckerRow.id.label("checker_id"),
                IdleCheckerRow.checker_type,
                IdleCheckerRow.spec,  # typed: ABCColumn loads it to a concrete IdleCheckerSpec
            )
            .join(IdleCheckerRow, IdleCheckerBindingRow.idle_checker_id == IdleCheckerRow.id)
            .where(IdleCheckerBindingRow.enabled == sa.true())
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
                    SessionRow.status.in_(session_statuses),
                    SessionRow.session_type != SessionTypes.INFERENCE,
                    self._enabled_binding_exists_query(),
                )
            )
            .order_by(SessionRow.created_at, SessionRow.id)
        )

        async with self._db.begin_readonly_session() as db_sess:
            binding_rows = (await db_sess.execute(binding_query)).fetchall()
            if not binding_rows:
                return IdleCheckSnapshot(
                    session_views_by_id={},
                    bindings_by_scope={},
                    checkers_by_id={},
                )
            session_rows = (await db_sess.execute(session_query)).fetchall()

        checkers_by_id: dict[IdleCheckerID, IdleCheckerRef] = {}
        bindings_by_scope: dict[ScopeRef, list[IdleCheckerBindingRef]] = {}
        for binding_row in binding_rows:
            checker_id = binding_row.checker_id
            checkers_by_id[checker_id] = IdleCheckerRef(
                checker_id=checker_id,
                checker_type=binding_row.checker_type,
                spec=binding_row.spec,
            )
            binding_scope = ScopeRef(ScopeType(binding_row.scope_type), binding_row.scope_id)
            bindings_by_scope.setdefault(binding_scope, []).append(
                IdleCheckerBindingRef(
                    binding_created_at=binding_row.binding_created_at,
                    checker_id=checker_id,
                )
            )

        session_views_by_id: dict[SessionId, IdleCheckSessionView] = {}
        for session_row in session_rows:
            session_id = SessionId(session_row.session_id)
            scopes = (
                ScopeRef(ScopeType.RESOURCE_GROUP, session_row.resource_group_id),
                ScopeRef(ScopeType.PROJECT, session_row.project_id),
                ScopeRef(ScopeType.DOMAIN, session_row.domain_id),
            )
            session_views_by_id[session_id] = IdleCheckSessionView(
                session_id=session_id,
                created_at=session_row.session_created_at,
                starts_at=session_row.session_starts_at,
                scopes=scopes,
            )

        return IdleCheckSnapshot(
            session_views_by_id=session_views_by_id,
            bindings_by_scope={
                scope: tuple(bindings) for scope, bindings in bindings_by_scope.items()
            },
            checkers_by_id=checkers_by_id,
        )

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
