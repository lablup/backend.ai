from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.manager.errors.image import ContainerRegistryNotFound
from ai.backend.manager.errors.repository import ForeignKeyViolationError
from ai.backend.manager.errors.resource import DomainNotFound
from ai.backend.manager.models.domain_container_registry_relation.row import (
    DomainContainerRegistryRelationRow,
)
from ai.backend.manager.models.specs.relation import RelationCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck, PreconditionCheck

__all__ = ("DomainContainerRegistryRelationCreator",)


@dataclass
class DomainContainerRegistryRelationCreator(
    RelationCreator[DomainID, ContainerRegistryID, DomainContainerRegistryRelationRow]
):
    """Links a domain (the scope) to a container registry (the target)."""

    @override
    def precondition_checks(
        self, scope: DomainID, target: ContainerRegistryID
    ) -> Sequence[PreconditionCheck]:
        return ()

    @override
    def row_class(self) -> type[DomainContainerRegistryRelationRow]:
        return DomainContainerRegistryRelationRow

    @override
    def build_row(
        self, scope: DomainID, target: ContainerRegistryID
    ) -> DomainContainerRegistryRelationRow:
        return DomainContainerRegistryRelationRow(domain_id=scope, container_registry_id=target)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=ForeignKeyViolationError,
                constraint_name="fk_domain_container_registry_relations_domain_id_domains",
                error=DomainNotFound("The domain to link registries to does not exist"),
            ),
            IntegrityErrorCheck(
                violation_type=ForeignKeyViolationError,
                constraint_name="fk_domain_container_registry_relations_container_registry_id",
                error=ContainerRegistryNotFound("A container registry to link does not exist"),
            ),
        )
