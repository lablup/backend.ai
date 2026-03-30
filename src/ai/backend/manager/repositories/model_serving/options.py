from __future__ import annotations

import uuid

import sqlalchemy as sa

from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.repositories.base import QueryCondition


class EndpointConditions:
    """Query conditions for endpoints (used in auto scaling rule searches with joins)."""

    @staticmethod
    def by_domain(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointRow.domain == domain_name

        return inner

    @staticmethod
    def by_session_owner(user_id: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointRow.session_owner == user_id

        return inner
