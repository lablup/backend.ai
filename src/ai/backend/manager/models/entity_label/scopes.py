"""Operation scopes for labels."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.scopes import ExistenceCheck, ScopeTarget

__all__ = ("EntityLabelTarget",)


@dataclass(frozen=True)
class EntityLabelTarget(ScopeTarget):
    """The labels on one entity.

    A label is readable exactly when its entity is, so the scopes a search runs in are
    the entities RBAC resolved for the requester.

    ``existence_checks`` is empty — RBAC validation already gates entity reachability.
    """

    owner: EntityIdentifier

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.owner

    @override
    def to_condition(self) -> QueryCondition:
        owner = self.owner

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                EntityLabelRow.entity_type == owner.entity_type(),
                EntityLabelRow.entity_id == owner,
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()
