"""Insert specs for container registries and their project associations."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.container_registry import AllowedGroupsModel, ContainerRegistryType
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.container_registry_group import ContainerRegistryGroupID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.exception import ContainerRegistryGroupsAlreadyAssociated
from ai.backend.manager.data.container_registry.types import (
    ContainerRegistryData,
    ContainerRegistryGroupData,
)
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.specs.creator import FieldCreator, GlobalEntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class ContainerRegistryCreator(
    GlobalEntityCreator[ContainerRegistryRow, ContainerRegistryData],
):
    """Creator for a container registry.

    A registry goes under no other scope, and the entities it owns (images) resolve
    through its own virtual scope; the projects allowed to reach them are bound to
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
class ContainerRegistryGroupCreator(
    FieldCreator[
        ContainerRegistryID,
        AssociationContainerRegistriesGroupsRow,
        ContainerRegistryGroupData,
    ],
):
    """Creator for the row associating a registry with one project."""

    project_id: ProjectID

    @override
    def field_id(self, row: AssociationContainerRegistriesGroupsRow) -> ContainerRegistryGroupID:
        return ContainerRegistryGroupID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                constraint_name="uq_registry_id_group_id",
                error=ContainerRegistryGroupsAlreadyAssociated(
                    f"Already associated groups for project_id: {self.project_id}"
                ),
            ),
        )

    @override
    def build_row(self, owner_id: ContainerRegistryID) -> AssociationContainerRegistriesGroupsRow:
        return AssociationContainerRegistriesGroupsRow(
            registry_id=owner_id,
            group_id=self.project_id,
        )

    @override
    def to_data(self, row: AssociationContainerRegistriesGroupsRow) -> ContainerRegistryGroupData:
        return ContainerRegistryGroupData(
            id=ContainerRegistryGroupID(row.id),
            registry_id=ContainerRegistryID(row.registry_id),
            project_id=ProjectID(row.group_id),
        )
