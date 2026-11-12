from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.container_registry import ContainerRegistryEntityType
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction, ScopedSearchOpsAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.data.container_registry.types import DomainContainerRegistryRelationData
from ai.backend.manager.models.domain_container_registry_relation.row import (
    DomainContainerRegistryRelationRow,
)


@dataclass(frozen=True)
class ScopedSearchDomainContainerRegistryRelationsAction(
    ScopedSearchOpsAction[DomainContainerRegistryRelationRow, DomainContainerRegistryRelationData]
):
    """Page through the relations of the named domains, combined with OR and narrowed by
    the container registries named as uses."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ContainerRegistryEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_domain_container_registry_relations"


@dataclass(frozen=True)
class GlobalSearchDomainContainerRegistryRelationsAction(
    GlobalSearcherOpsAction[DomainContainerRegistryRelationRow, DomainContainerRegistryRelationData]
):
    """Page through the relations of every domain, narrowed by the container registries
    named as uses."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ContainerRegistryEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_domain_container_registry_relations"


@dataclass(frozen=True)
class SearchDomainContainerRegistryRelationsActionResult(BaseScopeActionResult):
    items: list[DomainContainerRegistryRelationData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return [item.container_registry_id for item in self.items]
