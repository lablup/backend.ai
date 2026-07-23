from __future__ import annotations

import sqlalchemy as sa

from ai.backend.manager.models.clauses import QueryCondition

from .row import IdleCheckerBindingRow


class IdleCheckerBindingConditions:
    @staticmethod
    def enabled() -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return IdleCheckerBindingRow.enabled == sa.true()

        return inner
