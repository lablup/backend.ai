from __future__ import annotations

from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.common.data.idle_checker.types import IdleCheckPhase
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionId
from ai.backend.manager.models.clauses import QueryCondition

from .row import IdleCheckerBindingRow, SessionIdleCheckRow


class IdleCheckerBindingConditions:
    @staticmethod
    def enabled() -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return IdleCheckerBindingRow.enabled == sa.true()

        return inner


class SessionIdleCheckConditions:
    @staticmethod
    def by_pairs(
        pairs: Collection[tuple[SessionId, IdleCheckerID]],
    ) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.tuple_(
                SessionIdleCheckRow.session_id,
                SessionIdleCheckRow.idle_checker_id,
            ).in_(pairs)

        return inner

    @staticmethod
    def by_status_equals(status: IdleCheckPhase) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return SessionIdleCheckRow.last_status == status

        return inner
