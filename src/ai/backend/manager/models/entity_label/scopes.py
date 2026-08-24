"""Operation scopes for labels."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityID, EntityType
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope

__all__ = ("EntityLabelOperationScope",)


@dataclass(frozen=True)
class EntityLabelOperationScope(OperationScope):
    """The labels on one entity.

    A label is readable exactly when its entity is, so the scopes a search runs in are
    the entities RBAC resolved for the requester.

    ``existence_checks`` is empty — RBAC validation already gates entity reachability.
    """

    entity_type: EntityType
    entity_id: EntityID

    @override
    def to_condition(self) -> QueryCondition:
        entity_type = self.entity_type
        entity_id = self.entity_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                EntityLabelRow.entity_type == entity_type,
                EntityLabelRow.entity_id == entity_id,
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()
