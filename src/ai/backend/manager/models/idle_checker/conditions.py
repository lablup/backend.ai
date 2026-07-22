from __future__ import annotations

from datetime import datetime

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
    def expired(now: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return SessionIdleCheckRow.expire_at <= now

        return inner
