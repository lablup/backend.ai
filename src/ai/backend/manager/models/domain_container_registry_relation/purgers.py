from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.domain_container_registry_relation.row import (
    DomainContainerRegistryRelationRow,
)
from ai.backend.manager.models.specs.relation import RelationPurger
from ai.backend.manager.models.specs.types import ConflictCheck

__all__ = ("DomainContainerRegistryRelationPurger",)


@dataclass
class DomainContainerRegistryRelationPurger(
    RelationPurger[DomainID, ContainerRegistryID, DomainContainerRegistryRelationRow]
):
    """Unlinks a domain (the scope) from a container registry (the target)."""

    @override
    def row_class(self) -> type[DomainContainerRegistryRelationRow]:
        return DomainContainerRegistryRelationRow

    @override
    def conditions(self, scope: DomainID, target: ContainerRegistryID) -> Sequence[QueryCondition]:
        return (
            lambda: DomainContainerRegistryRelationRow.domain_id == scope,
            lambda: DomainContainerRegistryRelationRow.container_registry_id == target,
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()
