"""Searcher specs for the scaling_groups table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.models.resource_group.conditions import ResourceGroupConditions
from ai.backend.manager.models.resource_group.orders import ResourceGroupOrders
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.resource_group.scopes import (
    DomainResourceGroupOperationScope,
    ProjectResourceGroupOperationScope,
    UserResourceGroupOperationScope,
)
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.models.specs.searcher import Searcher

__all__ = (
    "AllowedResourceGroupsSearch",
    "ResourceGroupSearcher",
)


@dataclass
class ResourceGroupSearcher(Searcher[ResourceGroupRow, ResourceGroupData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ResourceGroupRow)

    @override
    def to_data(self, row: ResourceGroupRow) -> ResourceGroupData:
        return row.to_dataclass()


@dataclass(frozen=True)
class AllowedResourceGroupsSearch:
    """The active resource groups a user may schedule on in a domain and its projects.

    Run with ``search_with_scopes(operation_scopes(), searcher())``; items come in name order.
    """

    domain_id: DomainID
    project_ids: Sequence[ProjectID]
    user_id: UserID

    def operation_scopes(self) -> list[OperationScope]:
        return [
            DomainResourceGroupOperationScope(domain_id=self.domain_id),
            *(
                ProjectResourceGroupOperationScope(project_id=project_id)
                for project_id in self.project_ids
            ),
            UserResourceGroupOperationScope(user_id=self.user_id),
        ]

    def searcher(self) -> ResourceGroupSearcher:
        return ResourceGroupSearcher(
            pagination=NoPagination(),
            conditions=[ResourceGroupConditions.by_is_active(True)],
            orders=[ResourceGroupOrders.name()],
        )
