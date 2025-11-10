from __future__ import annotations

import logging
from typing import Optional

import sqlalchemy as sa

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.data.image.types import ImageStatus
from ai.backend.manager.errors.image import ContainerRegistryNotFound
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ContainerRegistryDBSource:
    """Database source for container registry-related operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def fetch_by_registry_and_project(
        self,
        registry_name: str,
        project: Optional[str] = None,
    ) -> ContainerRegistryData:
        """Fetch container registry data by registry name and optional project."""
        async with self._db.begin_readonly_session() as session:
            stmt = sa.select(ContainerRegistryRow).where(
                ContainerRegistryRow.registry_name == registry_name,
            )
            if project:
                stmt = stmt.where(ContainerRegistryRow.project == project)

            row: Optional[ContainerRegistryRow] = await session.scalar(stmt)
            if row is None:
                raise ContainerRegistryNotFound()
            return row.to_dataclass()

    async def fetch_by_registry_name(self, registry_name: str) -> list[ContainerRegistryData]:
        """Fetch all container registries with the given registry name."""
        async with self._db.begin_readonly_session() as session:
            stmt = sa.select(ContainerRegistryRow).where(
                ContainerRegistryRow.registry_name == registry_name
            )
            result = await session.execute(stmt)
            rows: list[ContainerRegistryRow] = result.scalars().all()
            return [row.to_dataclass() for row in rows]

    async def fetch_all(self) -> list[ContainerRegistryData]:
        """Fetch all container registries."""
        async with self._db.begin_readonly_session() as session:
            stmt = sa.select(ContainerRegistryRow)
            result = await session.execute(stmt)
            rows: list[ContainerRegistryRow] = result.scalars().all()
            return [row.to_dataclass() for row in rows]

    async def mark_images_as_deleted(
        self,
        registry_name: str,
        project: Optional[str] = None,
    ) -> None:
        """Mark all images as deleted for a given registry and optional project."""
        async with self._db.begin_session() as session:
            update_stmt = (
                sa.update(ImageRow)
                .where(ImageRow.registry == registry_name)
                .where(ImageRow.status != ImageStatus.DELETED)
                .values(status=ImageStatus.DELETED)
            )
            if project:
                update_stmt = update_stmt.where(ImageRow.project == project)

            await session.execute(update_stmt)

    async def fetch_known_registries(self) -> dict[str, str]:
        """Fetch all known container registries from the database."""
        async with self._db.begin_readonly_session() as session:
            known_registries_map = await ContainerRegistryRow.get_known_container_registries(
                session
            )

            known_registries = {}
            for project, registries in known_registries_map.items():
                for registry_name, url in registries.items():
                    if project not in known_registries:
                        known_registries[f"{project}/{registry_name}"] = url.human_repr()

            return known_registries

    async def fetch_registry_row(
        self,
        registry_name: str,
        project: Optional[str] = None,
    ) -> ContainerRegistryRow:
        """
        Fetch the raw ContainerRegistryRow object.
        Raise ContainerRegistryNotFound if registry is not found.
        """
        async with self._db.begin_readonly_session() as session:
            stmt = sa.select(ContainerRegistryRow).where(
                ContainerRegistryRow.registry_name == registry_name,
            )
            if project:
                stmt = stmt.where(ContainerRegistryRow.project == project)

            row: Optional[ContainerRegistryRow] = await session.scalar(stmt)
            if row is None:
                raise ContainerRegistryNotFound()
            return row
