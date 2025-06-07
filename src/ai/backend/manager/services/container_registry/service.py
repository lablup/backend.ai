import uuid

import sqlalchemy as sa

from ai.backend.manager.container_registry import get_container_registry_cls
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.container_registry.actions.clear_images import (
    ClearImagesAction,
    ClearImagesActionResult,
)
from ai.backend.manager.services.container_registry.actions.get_container_registries import (
    GetContainerRegistriesAction,
    GetContainerRegistriesActionResult,
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

from ...data.image.types import ImageStatus


class ContainerRegistryService:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def rescan_images(self, action: RescanImagesAction) -> RescanImagesActionResult:
        registry_name = action.registry
        project = action.project

        async with self._db.begin_readonly_session() as db_session:
            stmt = sa.select(ContainerRegistryRow).where(
                ContainerRegistryRow.registry_name == registry_name,
            )
            if project:
                stmt = stmt.where(ContainerRegistryRow.project == project)
            # TODO: Raise exception if registry not found or two or more registries found
            registry_row: ContainerRegistryRow = await db_session.scalar(stmt)

            scanner_cls = get_container_registry_cls(registry_row)
            scanner = scanner_cls(self._db, registry_name, registry_row)
            result = await scanner.rescan_single_registry(action.progress_reporter)

        return RescanImagesActionResult(
            images=result.images, errors=result.errors, registry=registry_row.to_dataclass()
        )

    async def clear_images(self, action: ClearImagesAction) -> ClearImagesActionResult:
        async with self._db.begin_session() as session:
            update_stmt = (
                sa.update(ImageRow)
                .where(ImageRow.registry == action.registry)
                .where(ImageRow.status != ImageStatus.DELETED)
                .values(status=ImageStatus.DELETED)
                .returning(ImageRow.id)
            )
            if action.project:
                update_stmt = update_stmt.where(ImageRow.project == action.project)

            cleared_row_ids: list[uuid.UUID] = (await session.scalars(update_stmt)).all()

            cleared_rows: list[ImageRow] = (
                await session.scalars(sa.select(ImageRow).where(ImageRow.id.in_(cleared_row_ids)))
            ).all()

            get_registry_row_stmt = sa.select(ContainerRegistryRow).where(
                ContainerRegistryRow.registry_name == action.registry,
            )
            if action.project:
                get_registry_row_stmt = get_registry_row_stmt.where(
                    ContainerRegistryRow.project == action.project
                )

            registry_row: ContainerRegistryRow = await session.scalar(get_registry_row_stmt)

        return ClearImagesActionResult(
            registry=registry_row.to_dataclass(),
            cleared_images=[row.to_dataclass() for row in cleared_rows],
        )

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

        return LoadContainerRegistriesActionResult(
            registries=[registry.to_dataclass() for registry in registries]
        )

    async def load_all_container_registries(
        self, action: LoadAllContainerRegistriesAction
    ) -> LoadAllContainerRegistriesActionResult:
        async with self._db.begin_readonly_session() as db_session:
            query = sa.select(ContainerRegistryRow)
            result = await db_session.execute(query)
            registries: list[ContainerRegistryRow] = result.scalars().all()
        return LoadAllContainerRegistriesActionResult(
            registries=[registry.to_dataclass() for registry in registries]
        )

    async def get_container_registries(
        self, action: GetContainerRegistriesAction
    ) -> GetContainerRegistriesActionResult:
        async with self._db.begin_session() as session:
            _registries = await ContainerRegistryRow.get_known_container_registries(session)

        known_registries = {}
        for project, registries in _registries.items():
            for registry_name, url in registries.items():
                if project not in known_registries:
                    known_registries[f"{project}/{registry_name}"] = url.human_repr()
        return GetContainerRegistriesActionResult(registries=known_registries)
