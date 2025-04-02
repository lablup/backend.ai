import sqlalchemy as sa

from ai.backend.manager.container_registry import get_container_registry_cls
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.image import ImageRow, ImageStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.container_registry.actions.clear_images import (
    ClearImagesAction,
    ClearImagesActionResult,
)
from ai.backend.manager.services.container_registry.actions.load_all_container_registries import (
    LoadAllContainerRegistriesAction,
    LoadAllContainerRegistriesActionResult,
)
from ai.backend.manager.services.container_registry.actions.load_container_registries import (
    LoadContainerRegistriesAction,
    LoadContainerRegistriesActionResult,
)
from ai.backend.manager.services.container_registry.actions.rescan_images import (
    RescanImagesAction,
    RescanImagesActionResult,
)


class ContainerRegistryService:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def rescan_images(self, action: RescanImagesAction) -> RescanImagesActionResult:
        registry_name = action.registry
        project = action.project

        async with self._db.begin_readonly_session() as db_session:
            registry_row = await db_session.scalar(
                sa.select(ContainerRegistryRow).where(
                    sa.and_(
                        ContainerRegistryRow.registry_name == registry_name,
                        ContainerRegistryRow.project == project,
                    )
                )
            )
            scanner_cls = get_container_registry_cls(registry_row)
            scanner = scanner_cls(self._db, registry_name, registry_row)
            result = await scanner.rescan_single_registry(None)

        return RescanImagesActionResult(
            images=result.images, errors=result.errors, registry_row=registry_row
        )

    async def clear_images(self, action: ClearImagesAction) -> ClearImagesActionResult:
        async with self._db.begin_session() as session:
            await session.execute(
                sa.update(ImageRow)
                .where(
                    sa.and_(
                        ImageRow.registry == action.registry, ImageRow.project == action.project
                    )
                )
                .where(ImageRow.status != ImageStatus.DELETED)
                .values(status=ImageStatus.DELETED)
            )

            registry_row = await session.scalar(
                sa.select(ContainerRegistryRow).where(
                    sa.and_(
                        ContainerRegistryRow.registry_name == action.registry,
                        ContainerRegistryRow.project == action.project,
                    )
                )
            )

        return ClearImagesActionResult(registry_row=registry_row)

    async def load_container_registries(
        self, action: LoadContainerRegistriesAction
    ) -> LoadContainerRegistriesActionResult:
        project = action.project

        async with self._db.begin_readonly_session() as db_session:
            query = sa.select(ContainerRegistryRow).where(
                ContainerRegistryRow.registry_name == action.registry
            )
            if project is not None:
                query = query.where(ContainerRegistryRow.project == project)
            result = await db_session.execute(query)
            registries = result.scalars().all()

        return LoadContainerRegistriesActionResult(registry_rows=registries)

    async def load_all_container_registries(
        self, action: LoadAllContainerRegistriesAction
    ) -> LoadAllContainerRegistriesActionResult:
        async with self._db.begin_readonly_session() as db_session:
            query = sa.select(ContainerRegistryRow)
            result = await db_session.execute(query)
            registries = result.scalars().all()
        return LoadAllContainerRegistriesActionResult(registry_rows=registries)
