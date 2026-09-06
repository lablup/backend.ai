"""Registry writes: the per-type row and the row that names it.

A registry is two rows — the per-type row (huggingface, reservoir) carrying the
connection settings and the ``artifact_registries`` row carrying its name and kind —
and every read of one reports the other's name. The pair is one primitive rather than
two calls a caller could get out of step, and it sits here rather than in the general
write ops because the artifact registries are the only thing shaped this way.
"""

from __future__ import annotations

import sqlalchemy as sa

from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryID
from ai.backend.manager.models.artifact_registries.creators import ArtifactRegistryMetaCreator
from ai.backend.manager.models.artifact_registries.row import ArtifactRegistryRow
from ai.backend.manager.models.artifact_registries.updaters import ArtifactRegistryMetaUpdater
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.creator import GlobalEntityCreator
from ai.backend.manager.models.specs.purger import EntityPurger
from ai.backend.manager.models.specs.updater import DataUpdater
from ai.backend.manager.repositories.ops.v2.write import V2WriteOps


class ArtifactRegistryWriteOps(V2WriteOps):
    """The general v2 write ops plus the registry-and-name pair."""

    async def create_registry[TRow: Base, TData](
        self,
        creator: GlobalEntityCreator[TRow, TData],
        meta_creator: ArtifactRegistryMetaCreator,
    ) -> TData:
        """Insert a registry, provision the node it becomes, and name it."""
        row = creator.build_row()
        await self._insert_row(row, creator.integrity_error_checks())
        registry_id = ArtifactRegistryID(creator.entity_id(row))
        await self._provision([registry_id])
        await self._insert_row(meta_creator.build_row(registry_id), ())
        await self._sess.refresh(row, ["meta"])
        return creator.to_data(row)

    async def update_registry[TRow: Base, TData](
        self,
        updater: DataUpdater[TRow, TData],
        meta_updater: ArtifactRegistryMetaUpdater,
    ) -> TData | None:
        """Edit a registry and its name; ``None`` if the registry is gone."""
        row = await self._update_row_returning(
            updater.row_class,
            updater.target_id_column(),
            updater.target_id_value(),
            updater.build_values(),
            updater.integrity_error_checks,
        )
        if row is None:
            return None
        await self._update_row_returning(
            meta_updater.row_class,
            meta_updater.target_id_column(),
            meta_updater.target_id_value(),
            meta_updater.build_values(),
            meta_updater.integrity_error_checks,
        )
        await self._sess.refresh(row, ["meta"])
        return updater.to_data(row)

    async def purge_registry[TRow: Base, TData](
        self, purger: EntityPurger[TRow, TData]
    ) -> TData | None:
        """Delete a registry, the row naming it, and the graph node it was."""
        await self._sess.execute(
            sa.delete(ArtifactRegistryRow).where(
                ArtifactRegistryRow.registry_id == purger.entity_id()
            )
        )
        return await self.purge_entity(purger)
