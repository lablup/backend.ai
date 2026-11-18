from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.container_registry import ContainerRegistryEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.container_registry.types import DomainContainerRegistryRelationData
from ai.backend.manager.models.domain_container_registry_relation.row import (
    DomainContainerRegistryRelationRow,
)


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
class GlobalSearchDomainContainerRegistryRelationsActionResult:
    items: list[DomainContainerRegistryRelationData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
