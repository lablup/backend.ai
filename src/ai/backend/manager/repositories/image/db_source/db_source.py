from __future__ import annotations

import functools
import logging
from collections import defaultdict
from collections.abc import Callable, Collection, Mapping, Sequence
from typing import cast
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import selectinload

from ai.backend.common.bgtask.reporter import ProgressReporter
from ai.backend.common.data.entity.image_alias import ImageAliasID
from ai.backend.common.docker import ImageRef
from ai.backend.common.types import ImageID
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
from ai.backend.manager.errors.image import (
    AliasImageActionDBError,
    AliasImageActionValueError,
    ImageAliasNotFound,
    ImageNotFound,
    PurgeImageActionByIdObjectDBError,
    RegistryNotFoundForImage,
    UpdateImageActionValueError,
)
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.image import (
    ImageAliasRow,
    ImageIdentifier,
    ImageRow,
)
from ai.backend.manager.models.image.conditions import ImageAliasConditions, ImageConditions
from ai.backend.manager.models.image.creators import ImageAliasCreator
from ai.backend.manager.models.image.lookups import ImageAliasOwnerLookup
from ai.backend.manager.models.image.orders import ImageOrders
from ai.backend.manager.models.image.purgers import ImagePurger
from ai.backend.manager.models.image.queriers import ImageQuerier
from ai.backend.manager.models.image.searchers import ImageAliasSearcher, ImageSearcher
from ai.backend.manager.models.image.updaters import ImageUpdater
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.models.specs.pagination import NoPagination, OffsetPagination
from ai.backend.manager.models.specs.searcher import SearcherResult
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, execute_batch_querier
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ImageDBSource:
    _db: ExtendedAsyncSAEngine
    _ops_provider: V2DBOpsProvider

    def __init__(self, db: ExtendedAsyncSAEngine, ops_provider: V2DBOpsProvider) -> None:
        self._db = db
        self._ops_provider = ops_provider

    async def fetch_image_by_reference(self, reference: str, architecture: str) -> ImageData:
        """The live image the reference names as a canonical for the architecture, or as an
        alias."""
        async with self._ops_provider.read_ops() as r:
            result = await r.search_in_global(
                self._reference_searcher(reference, architecture, [ImageStatus.ALIVE])
            )
        return self._first_image(result)

    async def fetch_image_by_canonical(self, canonical: str, architecture: str) -> ImageData:
        async with self._ops_provider.read_ops() as r:
            result = await r.search_in_global(
                self._canonical_searcher(canonical, architecture, [ImageStatus.ALIVE])
            )
        return self._first_image(result)

    async def fetch_images_by_canonicals(
        self, identifiers: Sequence[ImageIdentifier]
    ) -> list[ImageData]:
        images: list[ImageData] = []
        async with self._ops_provider.read_ops() as r:
            for identifier in identifiers:
                result = await r.search_in_global(
                    self._canonical_searcher(
                        identifier.canonical, identifier.architecture, [ImageStatus.ALIVE]
                    )
                )
                images.append(self._first_image(result))
        return images

    def _reference_searcher(
        self, reference: str, architecture: str, statuses: Collection[ImageStatus]
    ) -> ImageSearcher:
        return ImageSearcher(
            pagination=OffsetPagination(limit=1),
            conditions=[
                ImageConditions.by_canonical_and_architecture_or_alias(reference, architecture),
                *self._status_conditions(statuses),
            ],
            orders=ImageOrders.canonical_match_then_alive_then_oldest(reference, architecture),
        )

    def _canonical_searcher(
        self, canonical: str, architecture: str, statuses: Collection[ImageStatus]
    ) -> ImageSearcher:
        return ImageSearcher(
            pagination=OffsetPagination(limit=1),
            conditions=[
                ImageConditions.by_canonical_and_architecture(canonical, architecture),
                *self._status_conditions(statuses),
            ],
            orders=ImageOrders.alive_then_oldest(),
        )

    def _status_conditions(self, statuses: Collection[ImageStatus]) -> list[QueryCondition]:
        """An empty collection allows every status."""
        if not statuses:
            return []
        return [ImageConditions.by_statuses(statuses)]

    def _first_image(self, result: SearcherResult[ImageData]) -> ImageData:
        if not result.items:
            raise ImageNotFound()
        return result.items[0]

    async def _fetch_image(self, image_id: UUID, statuses: Collection[ImageStatus]) -> ImageData:
        async with self._ops_provider.read_ops() as r:
            image = await r.query_data(ImageQuerier(ImageID(image_id)))
        if image is None or (statuses and image.status not in statuses):
            raise ImageNotFound()
        return image

    async def _get_image_row_for_write(
        self, session: SASession, image_id: UUID, statuses: Collection[ImageStatus]
    ) -> ImageRow:
        row = await session.get(ImageRow, image_id)
        if row is None or (statuses and row.status not in statuses):
            raise ImageNotFound()
        return row

    async def _aliases_by_image(
        self, image_ids: Collection[ImageID]
    ) -> Mapping[ImageID, list[str]]:
        if not image_ids:
            return {}
        async with self._ops_provider.read_ops() as r:
            result = await r.search_in_global(
                ImageAliasSearcher(
                    pagination=NoPagination(),
                    conditions=[ImageAliasConditions.by_image_ids(image_ids)],
                )
            )
            owners = await r.lookup_field_owners(
                ImageAliasOwnerLookup(), [alias.id for alias in result.items]
            )
        aliases: defaultdict[ImageID, list[str]] = defaultdict(list)
        for alias in result.items:
            if alias.alias:
                aliases[ImageID(owners[alias.id])].append(alias.alias)
        return aliases

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
        statuses = [ImageStatus.ALIVE] if status_filter is None else status_filter
        async with self._ops_provider.read_ops() as r:
            result = await r.search_in_global(
                self._reference_searcher(identifier.canonical, identifier.architecture, statuses)
            )
        image = self._first_image(result)
        aliases = await self._aliases_by_image([image.id])
        return image.to_detailed(aliases.get(image.id, []))

    async def query_image_details_by_id(
        self,
        image_id: UUID,
        load_aliases: bool = False,
        status_filter: list[ImageStatus] | None = None,
    ) -> ImageDataWithDetails:
        statuses = [ImageStatus.ALIVE] if status_filter is None else status_filter
        image = await self._fetch_image(image_id, statuses)
        if not load_aliases:
            return image.to_detailed([])
        aliases = await self._aliases_by_image([image.id])
        return image.to_detailed(aliases.get(image.id, []))

    async def query_all_images(
        self, status_filter: list[ImageStatus] | None = None
    ) -> Mapping[ImageID, ImageDataWithDetails]:
        statuses = [ImageStatus.ALIVE] if status_filter is None else status_filter
        async with self._ops_provider.read_ops() as r:
            result = await r.search_in_global(
                ImageSearcher(
                    pagination=NoPagination(), conditions=self._status_conditions(statuses)
                )
            )
        aliases = await self._aliases_by_image([image.id for image in result.items])
        return {image.id: image.to_detailed(aliases.get(image.id, [])) for image in result.items}

    async def mark_image_deleted(self, reference: str, architecture: str) -> ImageData:
        """
        Deprecated. Use mark_image_deleted_by_id instead.
        """
        image = await self.fetch_image_by_reference(reference, architecture)
        return await self.mark_image_deleted_by_id(image.id)

    async def mark_image_deleted_by_id(
        self,
        image_id: UUID,
    ) -> ImageData:
        """
        Marks an image record as deleted by its ID in the database.
        """
        async with self._db.begin_session() as session:
            image_row = await self._get_image_row_for_write(session, image_id, [ImageStatus.ALIVE])
            await image_row.mark_as_deleted(session)
            return image_row.to_dataclass()

    async def mark_image_alive_by_id(
        self,
        image_id: UUID,
    ) -> ImageData:
        """
        Marks a soft-deleted image record as alive again by its ID in the database.
        """
        async with self._db.begin_session() as session:
            image_row = await self._get_image_row_for_write(
                session, image_id, ImageStatus.restorable()
            )
            await image_row.mark_as_alive(session)
            return image_row.to_dataclass()

    async def fetch_image_by_id(self, image_id: UUID, load_aliases: bool = False) -> ImageData:
        """
        Fetches an image from database by ID.
        Raises ImageNotFound if image doesn't exist.
        """
        return await self._fetch_image(image_id, [ImageStatus.ALIVE])

    async def validate_image_ownership(self, image_id: UUID, user_id: UUID) -> bool:
        """
        Checks if the image was committed for the user.
        Returns True if it was, False otherwise.
        Raises ImageNotFound if image doesn't exist.
        """
        image = await self._fetch_image(image_id, [ImageStatus.ALIVE])
        return image.customized and image.creator_id == user_id

    async def insert_image_alias(
        self, alias: str, image_canonical: str, architecture: str
    ) -> tuple[ImageID, ImageAliasData]:
        """
        Deprecated. Use insert_image_alias_by_id instead.
        """
        try:
            image = await self.fetch_image_by_canonical(image_canonical, architecture)
            image_id = image.id
            async with self._ops_provider.write_ops() as w:
                alias_data = await w.create_field(image_id, ImageAliasCreator(alias=alias))
            return image_id, alias_data
        except ValueError as e:
            raise AliasImageActionValueError from e
        except DBAPIError as e:
            raise AliasImageActionDBError(str(e)) from e

    async def query_image_alias(self, alias: str) -> ImageAliasData:
        async with self._db.begin_readonly_session_read_committed() as session:
            row = await self._get_image_alias_by_name(session, alias)
            return ImageAliasData(id=ImageAliasID(row.id), alias=row.alias or "")

    async def remove_image_alias(self, alias: str) -> tuple[UUID, ImageAliasData]:
        async with self._db.begin_session() as session:
            existing_alias = await self._get_image_alias_by_name(session, alias)
            image_id = existing_alias.image_id
            alias_data = ImageAliasData(
                id=ImageAliasID(existing_alias.id), alias=existing_alias.alias or ""
            )
            await session.delete(existing_alias)
        return image_id, alias_data

    async def scan_and_upsert_image(
        self, image_canonical: str, architecture: str
    ) -> RescanImagesResult:
        """
        Deprecated. Use scan_images_by_ids instead.
        """

        image = await self.fetch_image_by_canonical(image_canonical, architecture)
        registry_parts = []
        if image.registry:
            registry_parts.append(image.registry)
        if image.project:
            registry_parts.append(image.project)
        registry_key = "/".join(registry_parts) if registry_parts else ""

        async with self._db.begin_readonly_session_read_committed() as session:
            registry_row = await session.get(ContainerRegistryRow, image.registry_id)
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
        image = await self._fetch_image(image_id, [ImageStatus.ALIVE])
        async with self._db.begin_readonly_session() as session:
            registry_row = await session.get(ContainerRegistryRow, image.registry_id)
        if registry_row is None:
            raise RegistryNotFoundForImage(f"Registry not found for image {image_id}")
        return image, image.image_ref, registry_row

    async def modify_image_properties(self, updater: ImageUpdater) -> ImageData:
        try:
            async with self._ops_provider.write_ops() as w:
                data = await w.update_data(updater)
                if data is None:
                    raise ImageNotFound(f"Image not found (id:{updater.image_id})")
                return data
        except (ValueError, DBAPIError) as e:
            raise UpdateImageActionValueError from e

    async def clear_image_resource_limits(
        self, image_canonical: str, architecture: str
    ) -> ImageData:
        """
        Deprecated. Use clear_image_resource_limits_by_id instead.
        """
        image = await self.fetch_image_by_canonical(image_canonical, architecture)
        return await self.clear_image_resource_limits_by_id(image.id)

    async def insert_image_alias_by_id(
        self, image_id: ImageID, creator: ImageAliasCreator
    ) -> ImageAliasData:
        """
        Creates an alias of the image the id names.
        """
        try:
            await self._fetch_image(image_id, [ImageStatus.ALIVE])
            async with self._ops_provider.write_ops() as w:
                return await w.create_field(image_id, creator)
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
            image_row = await self._get_image_row_for_write(session, image_id, [ImageStatus.ALIVE])
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
            image_row = await self._get_image_row_for_write(session, image_id, [ImageStatus.ALIVE])
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
            async with self._ops_provider.write_ops() as w:
                data = await w.purge_entity(ImagePurger(image_id=ImageID(image_id)))
                if data is None:
                    raise ImageNotFound(f"Image not found (id: {image_id})")
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

    async def search_images_in_scopes(
        self, querier: BatchQuerier, scopes: Sequence[OperationScope]
    ) -> ImageListResult:
        """The search of :meth:`search_images`, restricted to the scopes (OR)."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(ImageRow).options(selectinload(ImageRow.aliases))
            result = await execute_batch_querier(db_sess, query, querier, scopes=scopes)
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
