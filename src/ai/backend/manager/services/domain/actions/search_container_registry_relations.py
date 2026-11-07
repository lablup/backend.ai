"""Action for searching the relations of domains to the container registries they are allowed on."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.container_registry import ContainerRegistryEntityType
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.data.container_registry.types import DomainContainerRegistryRelationData
from ai.backend.manager.models.domain_container_registry_relation.scopes import (
    DomainContainerRegistryRelationTarget,
)
from ai.backend.manager.models.domain_container_registry_relation.searchers import (
    DomainContainerRegistryRelationSearcher,
)


@dataclass(frozen=True)
class SearchDomainContainerRegistryRelationsAction(BaseScopeAction):
    """Page through the relations of the named domains, combined with OR.

    Every domain is authorized before the read runs, so a caller reaching for one they
    cannot see is refused rather than served the rest.
    """

    domain_ids: Sequence[DomainID]
    searcher: DomainContainerRegistryRelationSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ContainerRegistryEntityType()

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_domain_container_registry_relations"

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return list(self.domain_ids)

    def operation_scopes(self) -> Sequence[DomainContainerRegistryRelationTarget]:
        return [DomainContainerRegistryRelationTarget(domain_id) for domain_id in self.domain_ids]


@dataclass(frozen=True)
class SearchDomainContainerRegistryRelationsActionResult(BaseScopeActionResult):
    """A page of relations. What the read reached is the registries they link."""

    items: list[DomainContainerRegistryRelationData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return [item.container_registry_id for item in self.items]
