"""Resource-group search over the domains, projects and users they are associated with."""

from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction, ScopeItem
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.resource_group.scopes import (
    DomainResourceGroupOperationScope,
    ProjectResourceGroupOperationScope,
    UserResourceGroupOperationScope,
)
from ai.backend.manager.models.resource_group.searchers import ResourceGroupSearcher
from ai.backend.manager.models.scopes import OperationScope


class ResourceGroupScopeItem(ScopeItem, ABC):
    """One side a resource group is reachable from.

    A resource group is associated with domains, projects and keypairs independently,
    so which side a read comes in through is a value rather than a separate action.
    """


@dataclass(frozen=True)
class DomainResourceGroupScopeItem(ResourceGroupScopeItem):
    """The resource groups one domain may schedule on."""

    domain_id: DomainID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.domain_id

    @override
    def operation_scope(self) -> OperationScope:
        return DomainResourceGroupOperationScope(domain_id=self.domain_id)


@dataclass(frozen=True)
class ProjectResourceGroupScopeItem(ResourceGroupScopeItem):
    """The resource groups one project may schedule on."""

    project_id: ProjectID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.project_id

    @override
    def operation_scope(self) -> OperationScope:
        return ProjectResourceGroupOperationScope(project_id=self.project_id)


@dataclass(frozen=True)
class UserResourceGroupScopeItem(ResourceGroupScopeItem):
    """The resource groups one user's keypairs may schedule on."""

    user_id: UserID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.user_id

    @override
    def operation_scope(self) -> OperationScope:
        return UserResourceGroupOperationScope(user_id=self.user_id)


@dataclass(frozen=True)
class ScopedSearchResourceGroupsAction(
    OperationScopeOpsAction[ResourceGroupRow, ResourceGroupData]
):
    """Page through the resource groups the named scopes reach, combined with OR.

    Every scope is authorized before the read runs, so a caller reaching for one they
    cannot see is refused rather than served the rest.
    """

    items: Sequence[ResourceGroupScopeItem]
    searcher: ResourceGroupSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ResourceGroupEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_resource_groups"

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [item.scope_id() for item in self.items]

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return [item.operation_scope() for item in self.items]

    @override
    def to_searcher(self) -> ResourceGroupSearcher:
        return self.searcher
