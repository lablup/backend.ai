from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

import sqlalchemy as sa

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.types import AccessKey
from ai.backend.manager.models.resource_group import ResourceGroupForKeypairsRow
from ai.backend.manager.models.specs.types import ConflictCheck
from ai.backend.manager.repositories.base.purger import BatchPurger, BatchPurgerSpec


@dataclass
class ResourceGroupForKeypairsPurgerSpec(BatchPurgerSpec[ResourceGroupForKeypairsRow]):
    """PurgerSpec for disassociating a resource group from a keypair."""

    resource_group_id: ResourceGroupID
    access_key: AccessKey

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[ResourceGroupForKeypairsRow]]:
        return sa.select(ResourceGroupForKeypairsRow).where(
            sa.and_(
                ResourceGroupForKeypairsRow.resource_group_id == self.resource_group_id,
                ResourceGroupForKeypairsRow.access_key == self.access_key,
            )
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class ResourceGroupsForKeypairsPurgerSpec(BatchPurgerSpec[ResourceGroupForKeypairsRow]):
    """PurgerSpec for disassociating multiple resource groups from a keypair."""

    resource_group_ids: list[ResourceGroupID]
    access_key: AccessKey

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[ResourceGroupForKeypairsRow]]:
        return sa.select(ResourceGroupForKeypairsRow).where(
            sa.and_(
                ResourceGroupForKeypairsRow.resource_group_id.in_(self.resource_group_ids),
                ResourceGroupForKeypairsRow.access_key == self.access_key,
            )
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


def create_resource_group_for_keypairs_purger(
    resource_group_id: ResourceGroupID,
    access_key: AccessKey,
) -> BatchPurger[ResourceGroupForKeypairsRow]:
    """Create a BatchPurger for disassociating a resource group from a keypair."""
    return BatchPurger(
        spec=ResourceGroupForKeypairsPurgerSpec(
            resource_group_id=resource_group_id,
            access_key=access_key,
        ),
        batch_size=1,  # We expect only one row to be deleted
    )
