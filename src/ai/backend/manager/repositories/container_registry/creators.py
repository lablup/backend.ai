"""CreatorSpec implementations for container registry repository."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.container_registry import AllowedGroupsModel, ContainerRegistryType
from ai.backend.common.exception import ContainerRegistryGroupsAlreadyAssociated
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.repositories.base.creator import CreatorSpec
from ai.backend.manager.repositories.base.types import IntegrityErrorCheck


@dataclass
class ContainerRegistryCreatorSpec(CreatorSpec[ContainerRegistryRow]):
    """CreatorSpec for container registry creation."""

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

    @property
    def has_allowed_groups(self) -> bool:
        """Check if allowed_groups is set and has values to process."""
        return self.allowed_groups is not None and len(self.allowed_groups.add) > 0

    @override
    def build_row(self) -> ContainerRegistryRow:
        return ContainerRegistryRow(
            id=uuid.uuid4(),
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


@dataclass
class ContainerRegistryGroupCreatorSpec(
    CreatorSpec[AssociationContainerRegistriesGroupsRow],
):
    """CreatorSpec for container registry group association."""

    registry_id: uuid.UUID
    group_id: uuid.UUID

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                constraint_name="uq_registry_id_group_id",
                error=ContainerRegistryGroupsAlreadyAssociated(
                    f"Already associated groups for registry_id: {self.registry_id}, group_id: {self.group_id}"
                ),
            ),
        )

    @override
    def build_row(self) -> AssociationContainerRegistriesGroupsRow:
        return AssociationContainerRegistriesGroupsRow(
            registry_id=self.registry_id,
            group_id=self.group_id,
        )
