"""Operation scopes for domains."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType, ResourceGroupID
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.resource_group.row import ResourceGroupForDomainRow
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope
from ai.backend.manager.models.virtual_entity.queries import scope_membership_exists

__all__ = ("ResourceGroupDomainOperationScope",)


@dataclass(frozen=True)
class ResourceGroupDomainOperationScope(OperationScope):
    """The domains a resource group serves."""

    resource_group_id: ResourceGroupID

    @override
    def to_condition(self) -> QueryCondition:
        resource_group_id = self.resource_group_id

        # TODO(BA-7571): drop the association term once the ownership backfill lands.
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.or_(
                DomainRow.id.in_(
                    sa.select(ResourceGroupForDomainRow.domain_id).where(
                        ResourceGroupForDomainRow.resource_group_id == resource_group_id
                    )
                ),
                scope_membership_exists(
                    ResourceGroupEntityType(),
                    resource_group_id,
                    DomainEntityType(),
                    DomainRow.id,
                ),
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()
