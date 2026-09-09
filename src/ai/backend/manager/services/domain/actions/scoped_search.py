"""Domain search over the resource groups they are associated with."""

from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.resource_group import (
    RESOURCE_GROUP_SCOPE_TYPE,
    ResourceGroupID,
)
from ai.backend.common.data.entity.types import EntityType, ScopeRef
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction, ScopeItem
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.domain.scopes import ResourceGroupDomainOperationScope
from ai.backend.manager.models.domain.searchers import DomainSearcher
from ai.backend.manager.models.scopes import OperationScope


class DomainScopeItem(ScopeItem, ABC):
    """One side a domain is reachable from."""


@dataclass(frozen=True)
class ResourceGroupDomainScopeItem(DomainScopeItem):
    """The domains one resource group serves."""

    resource_group_id: ResourceGroupID

    @override
    def scope_ref(self) -> ScopeRef:
        return ScopeRef(scope_type=RESOURCE_GROUP_SCOPE_TYPE, scope_id=self.resource_group_id)

    @override
    def operation_scope(self) -> OperationScope:
        return ResourceGroupDomainOperationScope(resource_group_id=self.resource_group_id)


@dataclass(frozen=True)
class ScopedSearchDomainsAction(OperationScopeOpsAction[DomainRow, DomainData]):
    """Page through the domains the named scopes reach, combined with OR.

    Every scope is authorized before the read runs, so a caller reaching for one they
    cannot see is refused rather than served the rest.
    """

    items: Sequence[DomainScopeItem]
    searcher: DomainSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DomainEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_domains"

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return [item.scope_ref() for item in self.items]

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return [item.operation_scope() for item in self.items]

    @override
    def to_searcher(self) -> DomainSearcher:
        return self.searcher
