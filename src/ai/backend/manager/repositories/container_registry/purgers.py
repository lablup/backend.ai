"""BatchPurgerSpec implementations for container registry group associations."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

import sqlalchemy as sa

from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.repositories.base.purger import BatchPurgerSpec


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
