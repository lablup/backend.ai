"""Operation scopes for the relations between domains and container registries."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.errors.resource import DomainNotFound
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.domain_container_registry_relation.row import (
    DomainContainerRegistryRelationRow,
)
from ai.backend.manager.models.scopes import ExistenceCheck, ScopeTarget

__all__ = ("DomainContainerRegistryRelationTarget",)


@dataclass(frozen=True)
class DomainContainerRegistryRelationTarget(ScopeTarget):
    """The relations of one domain to the container registries it is allowed on."""

    domain_id: DomainID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.domain_id

    @override
    def to_condition(self) -> QueryCondition:
        domain_id = self.domain_id
        return lambda: DomainContainerRegistryRelationRow.domain_id == domain_id

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return [
            ExistenceCheck(
                column=DomainRow.id,
                value=self.domain_id,
                error=DomainNotFound(str(self.domain_id)),
            ),
        ]
