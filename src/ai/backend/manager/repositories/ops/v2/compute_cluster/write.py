"""Write ops that keep a resource group and the compute cluster it names consistent."""

from __future__ import annotations

import sqlalchemy as sa

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.dto.manager.v2.resource_group.request import (
    KUBERNETES_RESOURCE_GROUP_DRIVER,
)
from ai.backend.manager.data.compute_cluster.types import ComputeClusterData
from ai.backend.manager.models.compute_cluster.purgers import ComputeClusterPurger
from ai.backend.manager.models.compute_cluster.row import ComputeClusterRow
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.repositories.ops.v2.write import V2WriteOps


class V2ComputeClusterWriteOps(V2WriteOps):
    """The general v2 write ops plus the row locks that order a resource group write
    naming a compute cluster against the purge of that cluster.

    Lock order: the compute cluster row first, then the resource group rows.
    """

    async def share_lock_compute_cluster(self, name: str) -> bool:
        """Hold the named cluster row until commit so it cannot be purged meanwhile;
        False when no cluster has the name."""
        found = await self._sess.scalar(
            sa.select(ComputeClusterRow.id)
            .where(ComputeClusterRow.name == name)
            .with_for_update(read=True)
        )
        return found is not None

    async def stored_compute_cluster(self, resource_group_id: ResourceGroupID) -> str | None:
        """The cluster a `kubernetes` resource group names now, read without a lock."""
        return await self._sess.scalar(
            sa.select(ResourceGroupRow.driver_opts["compute_cluster"].astext).where(
                ResourceGroupRow.id == resource_group_id,
                ResourceGroupRow.driver == KUBERNETES_RESOURCE_GROUP_DRIVER,
            )
        )

    async def lock_resource_group(self, resource_group_id: ResourceGroupID) -> None:
        """Hold the resource group row until commit, so a session enqueue that holds it
        shared finishes first and the live-session guard sees its session."""
        await self._sess.execute(
            sa.select(ResourceGroupRow.id)
            .where(ResourceGroupRow.id == resource_group_id)
            .with_for_update()
        )

    async def purge_compute_cluster(
        self, purger: ComputeClusterPurger
    ) -> ComputeClusterData | None:
        """Purge the cluster with its row and the resource groups naming it locked, so a
        concurrent resource group write cannot start naming it after the conflict check."""
        name = await self._sess.scalar(
            sa.select(ComputeClusterRow.name)
            .where(ComputeClusterRow.id == purger.compute_cluster_id)
            .with_for_update()
        )
        if name is not None:
            await self._sess.execute(
                sa.select(ResourceGroupRow.id)
                .where(ResourceGroupRow.driver_opts["compute_cluster"].astext == name)
                .with_for_update()
            )
        return await self.purge_entity(purger)
