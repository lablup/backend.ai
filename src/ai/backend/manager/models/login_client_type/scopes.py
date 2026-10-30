"""Operation scopes for login client types."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.scopes import ExistenceCheck, ScopeTarget

__all__ = ("PublicLoginClientTypeTarget",)


@dataclass(frozen=True)
class PublicLoginClientTypeTarget(ScopeTarget):
    """Every login client type. The whole type is created in public, so no row is left out."""

    @override
    def scope_id(self) -> EntityIdentifier:
        return global_entity_id(GlobalEntityName.PUBLIC)

    @override
    def to_condition(self) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.true()

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()
