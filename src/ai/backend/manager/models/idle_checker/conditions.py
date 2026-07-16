from __future__ import annotations

import sqlalchemy as sa

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
    def expired() -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                SessionIdleCheckRow.expire_at.isnot(None),
                SessionIdleCheckRow.expire_at <= sa.func.now(),
            )

        return inner
