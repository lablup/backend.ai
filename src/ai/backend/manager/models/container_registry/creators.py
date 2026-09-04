"""Insert specs for a container registry and the project relation it takes part in."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.container_registry import AllowedGroupsModel, ContainerRegistryType
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.exception import ContainerRegistryGroupsAlreadyAssociated
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.specs.creator import GlobalEntityCreator
from ai.backend.manager.models.specs.relation import RelationCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class ContainerRegistryCreator(
    GlobalEntityCreator[ContainerRegistryRow, ContainerRegistryData],
):
    """Creator for a container registry.

    A registry goes under no other scope, and the entities it owns (images) resolve
    through its own virtual entity; the projects allowed to reach them are bound to
    that scope separately.
    """

    url: str
    type: ContainerRegistryType
    registry_name: str
    is_global: bool | None = None
    project: str | None = None
    username: str | None = None
    password: str | None = None
    ssl_verify: bool | None = None
    extra: dict[str, Any] | None = None
    allowed_groups: AllowedGroupsModel | None = None

    @override
    def entity_id(self, row: ContainerRegistryRow) -> ContainerRegistryID:
        return ContainerRegistryID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self) -> ContainerRegistryRow:
        return ContainerRegistryRow(
            id=ContainerRegistryID(uuid.uuid4()),
            url=self.url,
            type=self.type,
            registry_name=self.registry_name,
            is_global=self.is_global,
            project=self.project,
            username=self.username,
            password=self.password,
            ssl_verify=self.ssl_verify,
            extra=self.extra,
        )

    @override
    def to_data(self, row: ContainerRegistryRow) -> ContainerRegistryData:
        return row.to_dataclass()


@dataclass
class ContainerRegistryProjectCreator(
    RelationCreator[ProjectID, ContainerRegistryID, AssociationContainerRegistriesGroupsRow]
):
    """Links a project (the scope) to a registry (the target)."""

    @override
    def row_class(self) -> type[AssociationContainerRegistriesGroupsRow]:
        return AssociationContainerRegistriesGroupsRow

    @override
    def build_row(
        self, scope: ProjectID, target: ContainerRegistryID
    ) -> AssociationContainerRegistriesGroupsRow:
        return AssociationContainerRegistriesGroupsRow(registry_id=target, group_id=scope)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                constraint_name="uq_registry_id_group_id",
                error=ContainerRegistryGroupsAlreadyAssociated(
                    "The project is already allowed on the registry"
                ),
            ),
        )
