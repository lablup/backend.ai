"""PurgerSpec implementations for container registries and group associations."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

import sqlalchemy as sa

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.repositories.base.purger import BatchPurgerSpec
from ai.backend.manager.repositories.base.rbac.entity_purger import RBACEntityPurgerSpec
from ai.backend.manager.repositories.base.types import ConflictCheck


@dataclass
class ContainerRegistryGroupPurgerSpec(
    BatchPurgerSpec[AssociationContainerRegistriesGroupsRow],
):
    """PurgerSpec for removing a container registry association from a project."""

    registry_id: uuid.UUID
    group_id: uuid.UUID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[AssociationContainerRegistriesGroupsRow]]:
        return sa.select(AssociationContainerRegistriesGroupsRow).where(
            sa.and_(
                AssociationContainerRegistriesGroupsRow.registry_id == self.registry_id,
                AssociationContainerRegistriesGroupsRow.group_id == self.group_id,
            )
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class ContainerRegistryPurgerSpec(RBACEntityPurgerSpec[ContainerRegistryRow]):
    """PurgerSpec for purging a container registry with its RBAC entries."""

    registry_id: uuid.UUID

    @override
    def row_class(self) -> type[ContainerRegistryRow]:
        return ContainerRegistryRow

    @override
    def pk_value(self) -> uuid.UUID:
        return self.registry_id

    @override
    def element_type(self) -> RBACElementType:
        return RBACElementType.CONTAINER_REGISTRY

    @override
    def entity_ref(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.CONTAINER_REGISTRY,
            element_id=str(self.registry_id),
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()
