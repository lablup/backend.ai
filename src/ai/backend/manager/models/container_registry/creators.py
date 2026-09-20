"""Insert specs for a container registry and the project relation it takes part in."""

from __future__ import annotations

import uuid
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.errors.repository import ForeignKeyViolationError
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.specs.creator import EntityCreator
from ai.backend.manager.models.specs.relation import RelationCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck, PreconditionCheck


@dataclass
class ContainerRegistryCreator(EntityCreator[ContainerRegistryRow, ContainerRegistryData]):
    """Creator for a container registry.

    A registry is created in the `global` scope, and a global one in `public` as well,
    so every user reads it and the images it owns. The projects allowed to reach a
    registry that is not global are bound to it separately.
    """

    url: str
    type: ContainerRegistryType
    registry_name: str
    is_global: bool | None = None
    """Left out by the caller, the registry is global. The column itself is not nullable."""
    project: str | None = None
    username: str | None = None
    password: str | None = None
    ssl_verify: bool | None = None
    extra: dict[str, Any] | None = None

    @override
    def entity_id(self, row: ContainerRegistryRow) -> ContainerRegistryID:
        return ContainerRegistryID(row.id)

    @override
    def created_in(self, row: ContainerRegistryRow) -> Collection[EntityIdentifier]:
        if not row.is_global:
            return (global_entity_id(GlobalEntityName.GLOBAL),)
        return (
            global_entity_id(GlobalEntityName.GLOBAL),
            global_entity_id(GlobalEntityName.PUBLIC),
        )

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
            is_global=self._resolved_is_global(),
            project=self.project,
            username=self.username,
            password=self.password,
            ssl_verify=self.ssl_verify,
            extra=self.extra,
        )

    def _resolved_is_global(self) -> bool:
        """What the omitted input means, stated here so the row and `created_in` agree."""
        return True if self.is_global is None else self.is_global

    @override
    def to_data(self, row: ContainerRegistryRow) -> ContainerRegistryData:
        return row.to_dataclass()


@dataclass
class ContainerRegistryProjectCreator(
    RelationCreator[ProjectID, ContainerRegistryID, AssociationContainerRegistriesGroupsRow]
):
    """Links a project (the scope) to a registry (the target)."""

    @override
    def precondition_checks(
        self, scope: ProjectID, target: ContainerRegistryID
    ) -> Sequence[PreconditionCheck]:
        return ()

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
        """A project that is not there is the one violation a caller can act on. The
        unique constraint is not among them: a pair already linked is skipped in SQL, so
        naming one twice never reaches here."""
        return (
            IntegrityErrorCheck(
                violation_type=ForeignKeyViolationError,
                constraint_name="fk_association_container_registries_groups_group_id",
                error=ProjectNotFound("The project to allow on the registry does not exist"),
            ),
        )
