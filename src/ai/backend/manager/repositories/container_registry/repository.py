from typing import Optional

import sqlalchemy as sa

from ai.backend.common.decorators import create_layer_aware_repository_decorator
from ai.backend.common.metrics.metric import LayerType
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.data.image.types import ImageStatus
from ai.backend.manager.errors.image import ContainerRegistryNotFound
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, SASession

# Layer-specific decorator for container_registry repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.CONTAINER_REGISTRY)


class ContainerRegistryRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @repository_decorator()
    async def get_by_registry_and_project(
        self,
        registry_name: str,
        project: Optional[str] = None,
    ) -> ContainerRegistryData:
        async with self._db.begin_readonly_session() as session:
            return await self._get_by_registry_and_project(session, registry_name, project)

    @repository_decorator()
    async def get_by_registry_name(self, registry_name: str) -> list[ContainerRegistryData]:
        async with self._db.begin_readonly_session() as session:
            return await self._get_by_registry_name(session, registry_name)

    @repository_decorator()
    async def get_all(self) -> list[ContainerRegistryData]:
        async with self._db.begin_readonly_session() as session:
            return await self._get_all(session)

    @repository_decorator()
    async def clear_images(
        self,
        registry_name: str,
        project: Optional[str] = None,
    ) -> ContainerRegistryData:
        async with self._db.begin_session() as session:
            # Clear images
            update_stmt = (
                sa.update(ImageRow)
                .where(ImageRow.registry == registry_name)
                .where(ImageRow.status != ImageStatus.DELETED)
                .values(status=ImageStatus.DELETED)
            )
            if project:
                update_stmt = update_stmt.where(ImageRow.project == project)

            await session.execute(update_stmt)

            # Return registry data
            return await self._get_by_registry_and_project(session, registry_name, project)

    @repository_decorator()
    async def get_known_registries(self) -> dict[str, str]:
        async with self._db.begin_readonly_session() as session:
            from ai.backend.manager.models.container_registry import ContainerRegistryRow

            known_registries_map = await ContainerRegistryRow.get_known_container_registries(
                session
            )

            known_registries = {}
            for project, registries in known_registries_map.items():
                for registry_name, url in registries.items():
                    if project:
                        key = f"{project}/{registry_name}"
                    else:
                        key = registry_name
                    known_registries[key] = url.human_repr()

            return known_registries

    @repository_decorator()
    async def get_registry_row_for_scanner(
        self,
        registry_name: str,
        project: Optional[str] = None,
    ) -> ContainerRegistryRow:
        """
        Get the raw ContainerRegistryRow object needed for container registry scanner.
        Raises ContainerRegistryNotFound if registry is not found.
        """
        async with self._db.begin_readonly_session() as session:
            stmt = sa.select(ContainerRegistryRow).where(
                ContainerRegistryRow.registry_name == registry_name,
            )
            if project:
                stmt = stmt.where(ContainerRegistryRow.project == project)

            row = await session.scalar(stmt)
            if not row:
                raise ContainerRegistryNotFound()
            return row

    async def _get_by_registry_and_project(
        self,
        session: SASession,
        registry_name: str,
        project: Optional[str] = None,
    ) -> ContainerRegistryData:
        """
        Private method to get container registry by name and project.
        Raises ContainerRegistryNotFound if not found.
        """
        stmt = sa.select(ContainerRegistryRow).where(
            ContainerRegistryRow.registry_name == registry_name,
        )
        if project:
            stmt = stmt.where(ContainerRegistryRow.project == project)

        row = await session.scalar(stmt)
        if not row:
            raise ContainerRegistryNotFound()
        return row.to_dataclass()

    async def _get_by_registry_name(
        self,
        session: SASession,
        registry_name: str,
    ) -> list[ContainerRegistryData]:
        stmt = sa.select(ContainerRegistryRow).where(
            ContainerRegistryRow.registry_name == registry_name
        )
        result = await session.execute(stmt)
        rows = result.scalars().all()
        return [row.to_dataclass() for row in rows]

    async def _get_all(self, session: SASession) -> list[ContainerRegistryData]:
        stmt = sa.select(ContainerRegistryRow)
        result = await session.execute(stmt)
        rows = result.scalars().all()
        return [row.to_dataclass() for row in rows]
