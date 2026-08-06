"""PurgerSpec implementations for container registries and group associations."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

import sqlalchemy as sa

from ai.backend.common.data.entity.container_registry import CONTAINER_REGISTRY_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityRef
from ai.backend.common.identifier.container_registry import ContainerRegistryID
from ai.backend.common.identifier.project import ProjectID
from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.repositories.base.purger import BatchPurgerSpec
from ai.backend.manager.repositories.base.rbac.entity.purger import EntityPurgerSpec
from ai.backend.manager.repositories.base.types import ConflictCheck


@dataclass
class ContainerRegistryGroupPurgerSpec(
    BatchPurgerSpec[AssociationContainerRegistriesGroupsRow],
):
    """PurgerSpec for removing a container registry association from a project."""

    registry_id: ContainerRegistryID
    project_id: ProjectID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[AssociationContainerRegistriesGroupsRow]]:
        return sa.select(AssociationContainerRegistriesGroupsRow).where(
            sa.and_(
                AssociationContainerRegistriesGroupsRow.registry_id == self.registry_id,
                AssociationContainerRegistriesGroupsRow.group_id == self.project_id,
            )
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class ContainerRegistryPurgerSpec(EntityPurgerSpec[ContainerRegistryRow]):
    """PurgerSpec for deleting a container registry with its RBAC entries."""

    registry_id: ContainerRegistryID

    @override
    def row_class(self) -> type[ContainerRegistryRow]:
        return ContainerRegistryRow

    @override
    def pk_value(self) -> uuid.UUID:
        return self.registry_id

    @override
    def entity_ref(self) -> EntityRef:
        return EntityRef(
            entity_type=CONTAINER_REGISTRY_ENTITY_TYPE,
            entity_id=self.registry_id,
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()
