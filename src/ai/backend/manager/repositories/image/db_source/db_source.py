from __future__ import annotations

import functools
import logging
from collections.abc import Callable, Mapping
from typing import cast
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import selectinload

from ai.backend.common.bgtask.reporter import ProgressReporter
from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.docker import ImageRef
from ai.backend.common.exception import UnknownImageReference
from ai.backend.common.types import ImageAlias, ImageID
from ai.backend.common.utils import join_non_empty
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.container_registry import get_container_registry_cls
from ai.backend.manager.data.image.types import (
    ImageAliasData,
    ImageAliasListResult,
    ImageData,
    ImageDataWithDetails,
    ImageListResult,
    ImageStatus,
    RescanImagesResult,
    ResourceLimitInput,
)
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.errors.image import (
    AliasImageActionDBError,
    AliasImageActionValueError,
    ImageAliasNotFound,
    ImageNotFound,
    ModifyImageActionValueError,
    PurgeImageActionByIdObjectDBError,
    RegistryNotFoundForImage,
)
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.image import (
    ImageAliasRow,
    ImageIdentifier,
    ImageRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, execute_batch_querier
from ai.backend.manager.repositories.base.rbac.entity_creator import (
    RBACEntityCreator,
    execute_rbac_entity_creator,
)
from ai.backend.manager.repositories.base.updater import Updater, execute_updater
from ai.backend.manager.repositories.image.creators import ImageAliasCreatorSpec

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ImageDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def fetch_image_by_identifiers(
        self, identifiers: list[ImageAlias | ImageRef | ImageIdentifier]
    ) -> ImageData:
        """
        Fetches an image from database by its identifiers, which can be a combination of
        ImageAlias, ImageRef, or ImageIdentifier.
        Returns an ImageData object.
        Raises Exception if the image cannot be found.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            row = await self._resolve_image(session, identifiers)
            return row.to_dataclass()

    async def fetch_images_batch(
        self, identifier_lists: list[list[ImageIdentifier]]
    ) -> list[ImageData]:
        """
        Fetches multiple images from database by their identifiers in a single database session.
        Returns a list of ImageData objects.
        More efficient than multiple individual fetch operations.
        """
        async with self._db.begin_readonly_session() as session:
            rows: list[ImageRow] = []
            for identifiers in identifier_lists:
                row = await self._resolve_image(
                    session, cast(list[ImageAlias | ImageRef | ImageIdentifier], identifiers)
                )
                rows.append(row)
            return [row.to_dataclass() for row in rows]

    async def _resolve_image(
        self,
        session: SASession,
        identifiers: list[ImageAlias | ImageRef | ImageIdentifier],
    ) -> ImageRow:
        return await ImageRow.resolve(session, identifiers)

    async def _get_image_by_id(
        self,
        session: SASession,
        image_id: UUID,
        load_aliases: bool = False,
        status_filter: list[ImageStatus] | None = None,
    ) -> ImageRow:
        """
        Private method to get an image by ID using an existing session.
        Returns None if image is not found.
        """
        row = await ImageRow.get(
            session, image_id, load_aliases=load_aliases, filter_by_statuses=status_filter
        )
        if row is None:
            raise ImageNotFound()
        return row

    async def _get_image_alias_by_name(self, session: SASession, alias: str) -> ImageAliasRow:
        """
        Private method to get an image alias by name using an existing session.
        """
        image_alias_row = await session.scalar(
            sa.select(ImageAliasRow).where(ImageAliasRow.alias == alias),
        )
        if not image_alias_row:
            raise ImageAliasNotFound(f"Image alias '{alias}' not found.")
        return image_alias_row

    async def query_images_by_canonicals(
        self,
        canonicals: list[str],
        status_filter: list[ImageStatus] | None = None,
    ) -> dict[ImageID, ImageDataWithDetails]:
        """
        Deprecated. Use query_images_by_ids instead.
        """
        query = (
            sa.select(ImageRow)
            .where(ImageRow.name.in_(canonicals))
            .options(selectinload(ImageRow.aliases))
        )
        if status_filter:
            query = query.where(ImageRow.status.in_(status_filter))

        async with self._db.begin_readonly_session_read_committed() as session:
            result = await session.execute(query)
            image_rows = list(result.scalars().all())
            return {ImageID(row.id): row.to_detailed_dataclass() for row in image_rows}

    async def query_image_details_by_identifier(
        self,
        identifier: ImageIdentifier,
        status_filter: list[ImageStatus] | None = None,
    ) -> ImageDataWithDetails:
        """
        Deprecated. Use query_image_details_by_id instead.
        """
        try:
            async with self._db.begin_readonly_session_read_committed() as session:
                image_row = await ImageRow.resolve(
                    session,
                    [
                        identifier,
                        ImageAlias(identifier.canonical),
                    ],
                    filter_by_statuses=status_filter,
                )
        except UnknownImageReference as e:
            raise ImageNotFound from e
        return image_row.to_detailed_dataclass()

    async def query_image_details_by_id(
        self,
        image_id: UUID,
        load_aliases: bool = False,
        status_filter: list[ImageStatus] | None = None,
    ) -> ImageDataWithDetails:
        async with self._db.begin_readonly_session_read_committed() as session:
            try:
                row: ImageRow = await self._get_image_by_id(
                    session, image_id, load_aliases, status_filter
                )
            except UnknownImageReference as e:
                raise ImageNotFound() from e
            return row.to_detailed_dataclass()

    async def query_all_images(
        self, status_filter: list[ImageStatus] | None = None
    ) -> Mapping[ImageID, ImageDataWithDetails]:
        async with self._db.begin_readonly_session_read_committed() as session:
            rows = await ImageRow.list(session, load_aliases=True, filter_by_statuses=status_filter)
            return {ImageID(row.id): row.to_detailed_dataclass() for row in rows}

    async def mark_image_deleted(
        self,
        identifiers: list[ImageAlias | ImageRef | ImageIdentifier],
    ) -> ImageData:
        """
        Deprecated. Use mark_image_deleted_by_id instead.
        """
        async with self._db.begin_session() as session:
            row = await self._resolve_image(session, identifiers)
            await row.mark_as_deleted(session)
            return row.to_dataclass()

    async def mark_image_deleted_by_id(
        self,
        image_id: UUID,
    ) -> ImageData:
        """
        Marks an image record as deleted by its ID in the database.
        """
        async with self._db.begin_session() as session:
            image_row = await self._get_image_by_id(session, image_id)
            await image_row.mark_as_deleted(session)
            return image_row.to_dataclass()

    async def fetch_image_by_id(self, image_id: UUID, load_aliases: bool = False) -> ImageData:
        """
        Fetches an image from database by ID.
        Raises ImageNotFound if image doesn't exist.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            image_row = await self._get_image_by_id(session, image_id, load_aliases)
            return image_row.to_dataclass()

    async def validate_image_ownership(self, image_id: UUID, user_id: UUID) -> bool:
        """
        Checks if user owns the image.
        Returns True if user owns the image, False otherwise.
        Raises ImageNotFound if image doesn't exist.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            image_row = await self._get_image_by_id(session, image_id)
            return image_row.is_owned_by(user_id)

    async def insert_image_alias(
        self, alias: str, image_canonical: str, architecture: str
    ) -> tuple[UUID, ImageAliasData]:
        """
        Deprecated. Use insert_image_alias_by_id instead.
        """
        try:
            async with self._db.begin_session() as session:
                image_row = await ImageRow.resolve(
                    session, [ImageIdentifier(image_canonical, architecture)]
                )
                rbac_creator = RBACEntityCreator(
                    spec=ImageAliasCreatorSpec(
                        alias=alias,
                        image_id=image_row.id,
                    ),
                    element_type=RBACElementType.IMAGE_ALIAS,
                    scope_ref=RBACElementRef(
                        element_type=RBACElementType.IMAGE,
                        element_id=str(image_row.id),
                    ),
                )
                result = await execute_rbac_entity_creator(session, rbac_creator)
                row_id = image_row.id
                alias_data = ImageAliasData(id=result.row.id, alias=result.row.alias or "")
            return row_id, alias_data
        except ValueError as e:
            raise AliasImageActionValueError from e
        except DBAPIError as e:
            raise AliasImageActionDBError(str(e)) from e

    async def query_image_alias(self, alias: str) -> ImageAliasData:
        async with self._db.begin_readonly_session_read_committed() as session:
            row = await self._get_image_alias_by_name(session, alias)
            return ImageAliasData(id=row.id, alias=row.alias or "")

    async def remove_image_alias(self, alias: str) -> tuple[UUID, ImageAliasData]:
        async with self._db.begin_session() as session:
            existing_alias = await self._get_image_alias_by_name(session, alias)
            image_id = existing_alias.image_id
            alias_data = ImageAliasData(id=existing_alias.id, alias=existing_alias.alias or "")
            await session.delete(existing_alias)
        return image_id, alias_data

    async def scan_and_upsert_image(
        self, image_canonical: str, architecture: str
    ) -> RescanImagesResult:
        """
        Deprecated. Use scan_images_by_ids instead.
        """

        async with self._db.begin_session() as session:
            # Resolve the image first
            image_row = await self._resolve_image(
                session, [ImageIdentifier(image_canonical, architecture)]
            )

            # Get the registry info
            registry_parts = []
            if image_row.registry:
                registry_parts.append(image_row.registry)
            if image_row.project:
                registry_parts.append(image_row.project)
            registry_key = "/".join(registry_parts) if registry_parts else ""

            # Get the registry row
            registry_row = await session.get(ContainerRegistryRow, image_row.registry_id)
            if not registry_row:
                raise RegistryNotFoundForImage(f"Registry not found for image {image_canonical}")

            return await self.scan_single_image(registry_key, registry_row, image_canonical)

    async def fetch_image_and_registry(
        self, image_id: UUID
    ) -> tuple[ImageData, ImageRef, ContainerRegistryRow]:
        """Read the image (as data + ref) and its container registry row.

        Used by the repository to orchestrate a registry untag without holding a
        DB session open across the external registry call.
        """
        async with self._db.begin_readonly_session() as session:
            image_row = await self._get_image_by_id(session, image_id, load_aliases=True)
            registry_row = await session.get(ContainerRegistryRow, image_row.registry_id)
            if registry_row is None:
                raise RegistryNotFoundForImage(f"Registry not found for image {image_id}")
            return image_row.to_dataclass(), image_row.image_ref, registry_row

    async def modify_image_properties(self, updater: Updater[ImageRow]) -> ImageData:
        try:
            async with self._db.begin_session() as session:
                result = await execute_updater(session, updater)
                if result is None:
                    raise ImageNotFound(f"Image not found (id:{updater.pk_value})")
                return result.row.to_dataclass()
        except (ValueError, DBAPIError) as e:
            raise ModifyImageActionValueError from e

    async def clear_image_resource_limits(
        self, image_canonical: str, architecture: str
    ) -> ImageData:
        """
        Deprecated. Use clear_image_resource_limits_by_id instead.
        """
        async with self._db.begin_session() as session:
            image_row = await ImageRow.resolve(
                session, [ImageIdentifier(image_canonical, architecture)]
            )
            image_row._resources = {}
            return image_row.to_dataclass()

    async def insert_image_alias_by_id(
        self, creator: RBACEntityCreator[ImageAliasRow]
    ) -> ImageAliasData:
        """
        Creates an image alias using the RBACEntityCreator pattern.
        """
        try:
            async with self._db.begin_session() as session:
                spec = cast(ImageAliasCreatorSpec, creator.spec)
                # Validate that the image exists
                await self._get_image_by_id(session, spec.image_id)
                result = await execute_rbac_entity_creator(session, creator)
                return ImageAliasData(id=result.row.id, alias=result.row.alias or "")
        except ValueError as e:
            raise AliasImageActionValueError from e
        except DBAPIError as e:
            raise AliasImageActionDBError(str(e)) from e

    async def query_images_by_ids(
        self,
        image_ids: list[UUID],
        status_filter: list[ImageStatus] | None = None,
    ) -> dict[ImageID, ImageDataWithDetails]:
        """
        Queries images by their IDs with optional status filter.
        Returns a dictionary mapping ImageID to ImageDataWithDetails.
        """
        if not image_ids:
            return {}

        query = (
            sa.select(ImageRow)
            .where(ImageRow.id.in_(image_ids))
            .options(selectinload(ImageRow.aliases))
        )
        if status_filter:
            query = query.where(ImageRow.status.in_(status_filter))

        async with self._db.begin_readonly_session_read_committed() as session:
            result = await session.execute(query)
            image_rows = list(result.scalars().all())
            return {ImageID(row.id): row.to_detailed_dataclass() for row in image_rows}

    async def clear_image_resource_limits_by_id(self, image_id: UUID) -> ImageData:
        """
        Clears image resource limits by image ID.
        """
        async with self._db.begin_session() as session:
            image_row = await self._get_image_by_id(session, image_id)
            image_row._resources = {}
            return image_row.to_dataclass()

    async def set_image_resource_limit_by_id(
        self,
        image_id: UUID,
        resource_limit: ResourceLimitInput,
    ) -> ImageData:
        """
        Sets resource limit for an image by its ID.
        """
        async with self._db.begin_session() as session:
            image_row = await self._get_image_by_id(session, image_id)
            resources = dict(image_row._resources) if image_row._resources else {}

            if resource_limit.slot_name not in resources:
                resources[resource_limit.slot_name] = {"min": None, "max": None}

            if resource_limit.min_value is not None:
                resources[resource_limit.slot_name]["min"] = str(resource_limit.min_value)
            if resource_limit.max_value is not None:
                resources[resource_limit.slot_name]["max"] = str(resource_limit.max_value)

            image_row._resources = resources
            return image_row.to_dataclass()

    async def remove_image_and_aliases(
        self,
        image_id: UUID,
    ) -> ImageData:
        """
        Removes an image record and all its aliases from the database.
        """
        try:
            async with self._db.begin_session() as session:
                image_row = await self._get_image_by_id(session, image_id, load_aliases=True)
                data = image_row.to_dataclass()
                for alias in image_row.aliases:
                    await session.delete(alias)
                await session.delete(image_row)
            return data
        except DBAPIError as e:
            raise PurgeImageActionByIdObjectDBError(str(e)) from e

    async def search_images(self, querier: BatchQuerier) -> ImageListResult:
        """
        Search images using a batch querier with conditions, pagination, and ordering.
        Returns ImageListResult with items and pagination info.
        """
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(ImageRow).options(selectinload(ImageRow.aliases))
            result = await execute_batch_querier(db_sess, query, querier)
            items = [row.ImageRow.to_dataclass() for row in result.rows]
            return ImageListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def search_aliases(self, querier: BatchQuerier) -> ImageAliasListResult:
        """
        Search image aliases using a batch querier with conditions, pagination, and ordering.
        Returns ImageAliasListResult with items and pagination info.
        """
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(ImageAliasRow)
            result = await execute_batch_querier(db_sess, query, querier)
            items = [row.ImageAliasRow.to_dataclass() for row in result.rows]
            image_ids = [ImageID(row.ImageAliasRow.image_id) for row in result.rows]
            return ImageAliasListResult(
                items=items,
                image_ids=image_ids,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def rescan_images(
        self,
        registry_or_image: str | None = None,
        project: str | None = None,
        *,
        reporter: ProgressReporter | None = None,
    ) -> RescanImagesResult:
        """
        Rescan container registries and update the images table.

        If registry name is provided for ``registry_or_image``, scans all images in that registry.
        If image canonical name is provided, only scan that image.
        If ``registry_or_image`` is not provided, scan all configured registries.
        If ``project`` is provided, only scan the registries associated with the project.
        """
        registries = await self._load_configured_registries(project)

        if registry_or_image is None:
            return await self._scan_registries(registries, reporter=reporter)

        matching_registries = self._filter_by_img_canonical(registries, registry_or_image)

        if matching_registries:
            if len(matching_registries) > 1:
                raise RuntimeError(
                    "ContainerRegistryRows exist with the same registry_name and project!",
                )

            registry_key, registry_row = next(iter(matching_registries.items()))
            return await self.scan_single_image(registry_key, registry_row, registry_or_image)

        matching_registries = self._filter_by_registry_name(registries, registry_or_image)

        if not matching_registries:
            raise RuntimeError("It is an unknown registry.", registry_or_image)

        log.debug("running a per-registry metadata scan")
        return await self._scan_registries(matching_registries, reporter=reporter)
        # TODO: delete images removed from registry?

    async def scan_single_image(
        self,
        registry_key: str,
        registry_row: ContainerRegistryRow,
        image_canonical: str,
    ) -> RescanImagesResult:
        """Performs a scan for a single image."""
        registry_name = ImageRef.parse_image_str(registry_key, "*").registry
        image_name = image_canonical.removeprefix(registry_name + "/")

        log.debug("running a per-image metadata scan: {}, {}", registry_name, image_name)

        scanner_cls = get_container_registry_cls(registry_row)
        scanner = scanner_cls(self._db, registry_name, registry_row)
        return await scanner.scan_single_ref(image_name)

    async def _load_configured_registries(
        self, project: str | None
    ) -> dict[str, ContainerRegistryRow]:
        join = functools.partial(join_non_empty, sep="/")

        async with self._db.begin_readonly_session() as session:
            result = await session.execute(sa.select(ContainerRegistryRow))
            if project:
                registries = cast(
                    dict[str, ContainerRegistryRow],
                    {
                        join(row.registry_name, row.project): row
                        for row in result.scalars().all()
                        if row.project == project
                    },
                )
            else:
                registries = {
                    join(row.registry_name, row.project): row for row in result.scalars().all()
                }

        return registries

    async def _scan_registries(
        self,
        registries: dict[str, ContainerRegistryRow],
        reporter: ProgressReporter | None = None,
    ) -> RescanImagesResult:
        """Performs an image rescan for all images in the registries."""
        images, errors = [], []

        for registry_key, registry_row in registries.items():
            registry_name = ImageRef.parse_image_str(registry_key, "*").registry
            log.info('Scanning kernel images from the registry "{0}"', registry_name)

            scanner_cls = get_container_registry_cls(registry_row)
            scanner = scanner_cls(self._db, registry_name, registry_row)

            try:
                scan_result = await scanner.rescan_single_registry(reporter)
                images.extend(scan_result.images or [])
                errors.extend(scan_result.errors or [])
            except Exception as e:
                errors.append(str(e))

        return RescanImagesResult(images=images, errors=errors)

    @staticmethod
    def _filter_registry_dict(
        registries: dict[str, ContainerRegistryRow],
        condition: Callable[[str, ContainerRegistryRow], bool],
    ) -> dict[str, ContainerRegistryRow]:
        return {
            registry_key: registry_row
            for registry_key, registry_row in registries.items()
            if condition(registry_key, registry_row)
        }

    @classmethod
    def _filter_by_img_canonical(
        cls, registries: dict[str, ContainerRegistryRow], registry_or_image: str
    ) -> dict[str, ContainerRegistryRow]:
        """Filter registries assuming ``registry_or_image`` is an image canonical name."""
        return cls._filter_registry_dict(
            registries,
            lambda registry_key, _row: registry_or_image.startswith(registry_key + "/"),
        )

    @classmethod
    def _filter_by_registry_name(
        cls, registries: dict[str, ContainerRegistryRow], registry_or_image: str
    ) -> dict[str, ContainerRegistryRow]:
        """Filter registries assuming ``registry_or_image`` is a registry name."""
        return cls._filter_registry_dict(
            registries,
            lambda registry_key, _row: registry_key.startswith(registry_or_image),
        )
