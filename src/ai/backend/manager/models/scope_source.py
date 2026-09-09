"""A Row queryable as an RBAC scope."""

from __future__ import annotations

from typing import Protocol

from sqlalchemy.sql.expression import SQLColumnExpression

from ai.backend.common.data.entity.types import EntityID


class ScopeSource(Protocol):
    """A Row queryable as an RBAC scope: its scope-id and display-name expressions."""

    @classmethod
    def scope_id_expr(cls) -> SQLColumnExpression[EntityID]:
        """Column carrying the scope's id."""
        ...

    @classmethod
    def scope_name_expr(cls) -> SQLColumnExpression[str]:
        """Expression rendering the scope's display name."""
        ...
