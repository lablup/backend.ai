from __future__ import annotations

import uuid
from typing import ClassVar

from sqlalchemy.sql.expression import SQLColumnExpression

from ai.backend.common.data.entity.types import ScopeType


class ScopeRowMixin:
    """Marks a Row as an RBAC scope source.

    Declares only the schema metadata needed to query the row as a scope —
    query builders stay in the repositories layer.
    """

    __scope_type__: ClassVar[ScopeType]

    @classmethod
    def scope_id_expr(cls) -> SQLColumnExpression[uuid.UUID]:
        """Column whose value is used as ``ScopeRef.scope_id``."""
        raise NotImplementedError

    @classmethod
    def scope_name_expr(cls) -> SQLColumnExpression[str]:
        """Expression rendering the scope's display name."""
        raise NotImplementedError
