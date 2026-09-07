"""Operation scopes for domains."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.resource_group.row import ResourceGroupForDomainRow
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope

__all__ = ("ResourceGroupDomainOperationScope",)


@dataclass(frozen=True)
class ResourceGroupDomainOperationScope(OperationScope):
    """The domains a resource group serves."""

    resource_group_id: ResourceGroupID

    @override
    def to_condition(self) -> QueryCondition:
        resource_group_id = self.resource_group_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainRow.id.in_(
                sa.select(ResourceGroupForDomainRow.domain_id).where(
                    ResourceGroupForDomainRow.resource_group_id == resource_group_id
                )
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()
