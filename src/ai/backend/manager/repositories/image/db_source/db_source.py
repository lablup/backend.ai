import logging
from collections.abc import Mapping
from typing import Optional, cast
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import selectinload

from ai.backend.common.docker import ImageRef
from ai.backend.common.exception import UnknownImageReference
from ai.backend.common.types import ImageAlias, ImageID
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.image.types import (
    ImageAliasData,
    ImageData,
    ImageDataWithDetails,
    ImageStatus,
    RescanImagesResult,
)
from ai.backend.manager.errors.image import (
    AliasImageActionDBError,
    AliasImageActionValueError,
    ForgetImageForbiddenError,
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
    scan_single_image,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.updater import Updater, execute_updater

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
        async with self._db.begin_session() as session:
            row = await self._resolve_image(session, identifiers)
            data = row.to_dataclass()
        return data

    async def fetch_images_batch(
        self, identifier_lists: list[list[ImageIdentifier]]
    ) -> list[ImageData]:
        """
        Fetches multiple images from database by their identifiers in a single database session.
        Returns a list of ImageData objects.
        More efficient than multiple individual fetch operations.
        """
        async with self._db.begin_session() as session:
            rows: list[ImageRow] = []
            for identifiers in identifier_lists:
                row = await self._resolve_image(
                    session, cast(list[ImageAlias | ImageRef | ImageIdentifier], identifiers)
                )
                rows.append(row)
            data_list = [row.to_dataclass() for row in rows]
        return data_list

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
        status_filter: Optional[list[ImageStatus]] = None,
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

    async def _validate_image_ownership(
        self, session: SASession, image_id: UUID, user_id: UUID, load_aliases: bool = False
    ) -> ImageRow:
        """
        Private method to get an image and validate ownership using an existing session.
        Raises ForgetImageActionGenericForbiddenError if image doesn't exist or user doesn't own it.
        """
        image_row = await self._get_image_by_id(session, image_id, load_aliases)
        if not image_row.is_owned_by(user_id):
            raise ForgetImageForbiddenError()
        return image_row

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
        status_filter: Optional[list[ImageStatus]] = None,
    ) -> dict[ImageID, ImageDataWithDetails]:
        query = (
            sa.select(ImageRow)
            .where(ImageRow.name.in_(canonicals))
            .options(selectinload(ImageRow.aliases))
        )
        if status_filter:
            query = query.where(ImageRow.status.in_(status_filter))

        async with self._db.begin_readonly_session() as session:
            result = await session.execute(query)
            image_rows: list[ImageRow] = result.scalars().all()
            return {ImageID(row.id): row.to_detailed_dataclass() for row in image_rows}

    async def query_image_details_by_identifier(
        self,
        identifier: ImageIdentifier,
        status_filter: Optional[list[ImageStatus]] = None,
    ) -> ImageDataWithDetails:
        try:
            async with self._db.begin_readonly_session() as session:
                image_row = await ImageRow.resolve(
                    session,
                    [
                        identifier,
                        ImageAlias(identifier.canonical),
                    ],
                    filter_by_statuses=status_filter,
                )
        except UnknownImageReference:
            raise ImageNotFound
        data = image_row.to_detailed_dataclass()
        return data

    async def query_image_details_by_id(
        self,
        image_id: UUID,
        load_aliases: bool = False,
        status_filter: Optional[list[ImageStatus]] = None,
    ) -> ImageDataWithDetails:
        async with self._db.begin_session() as session:
            try:
                row: ImageRow = await self._get_image_by_id(
                    session, image_id, load_aliases, status_filter
                )
            except UnknownImageReference:
                raise ImageNotFound()
            data = row.to_detailed_dataclass()
        return data

    async def query_all_images(
        self, status_filter: Optional[list[ImageStatus]] = None
    ) -> Mapping[ImageID, ImageDataWithDetails]:
        async with self._db.begin_readonly_session() as session:
            rows = await ImageRow.list(session, load_aliases=True, filter_by_statuses=status_filter)
            return {ImageID(row.id): row.to_detailed_dataclass() for row in rows}

    async def mark_user_image_deleted(
        self,
        identifiers: list[ImageAlias | ImageRef | ImageIdentifier],
        user_id: UUID,
    ) -> ImageData:
        """
        Marks an image record as deleted for a specific user in the database.
        Raises ForgetImageActionGenericForbiddenError if the user does not own the image.
        """
        async with self._db.begin_session() as session:
            row = await self._resolve_image(session, identifiers)
            if not row.is_owned_by(user_id):
                raise ForgetImageForbiddenError()
            await row.mark_as_deleted(session)
            data = row.to_dataclass()
        return data

    async def mark_image_deleted_by_id(
        self,
        image_id: UUID,
        user_id: UUID,
    ) -> ImageData:
        """
        Marks an image record as deleted by its ID in the database.
        Validates ownership by user_id before deletion.
        Raises ForgetImageActionGenericForbiddenError if the user does not own the image.
        """
        async with self._db.begin_session() as session:
            image_row = await self._validate_image_ownership(session, image_id, user_id)
            await image_row.mark_as_deleted(session)
            data = image_row.to_dataclass()
        return data

    async def validate_and_fetch_image_ownership(
        self, image_id: UUID, user_id: UUID, load_aliases: bool = False
    ) -> ImageData:
        """
        Validates ownership and fetches an image from database by ID in a single operation.
        Raises ForgetImageActionGenericForbiddenError if image doesn't exist or user doesn't own it.
        """
        async with self._db.begin_session() as session:
            image_row = await self._validate_image_ownership(
                session, image_id, user_id, load_aliases
            )
            data = image_row.to_dataclass()
        return data

    async def insert_image_alias(
        self, alias: str, image_canonical: str, architecture: str
    ) -> tuple[UUID, ImageAliasData]:
        try:
            async with self._db.begin_session() as session:
                image_row = await ImageRow.resolve(
                    session, [ImageIdentifier(image_canonical, architecture)]
                )
                image_alias = ImageAliasRow(alias=alias, image_id=image_row.id)
                image_row.aliases.append(image_alias)
                row_id = image_row.id
                alias_data = ImageAliasData(id=image_alias.id, alias=image_alias.alias)
            return row_id, alias_data
        except ValueError:
            raise AliasImageActionValueError
        except DBAPIError as e:
            raise AliasImageActionDBError(str(e))

    async def query_image_alias(self, alias: str) -> ImageAliasData:
        async with self._db.begin_session() as session:
            row = await self._get_image_alias_by_name(session, alias)
            data = ImageAliasData(id=row.id, alias=row.alias)
        return data

    async def remove_image_alias(self, alias: str) -> tuple[UUID, ImageAliasData]:
        async with self._db.begin_session() as session:
            existing_alias = await self._get_image_alias_by_name(session, alias)
            image_id = existing_alias.image_id
            alias_data = ImageAliasData(id=existing_alias.id, alias=existing_alias.alias)
            await session.delete(existing_alias)
        return image_id, alias_data

    async def scan_and_upsert_image(
        self, image_canonical: str, architecture: str
    ) -> RescanImagesResult:
        """
        Scans a single image and upserts it into the database.
        Returns RescanImagesResult with the scanned image data.
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

            # Call the original scan function
            result = await scan_single_image(self._db, registry_key, registry_row, image_canonical)

        return result

    async def remove_tag_from_registry(self, image_id: UUID) -> ImageData:
        async with self._db.begin_readonly_session() as session:
            image_row = await self._get_image_by_id(session, image_id, load_aliases=True)
            if not image_row:
                raise ImageNotFound()
            await image_row.untag_image_from_registry(self._db, session)
            data = image_row.to_dataclass()
        return data

    async def modify_image_properties(self, updater: Updater[ImageRow]) -> ImageData:
        try:
            async with self._db.begin_session() as session:
                result = await execute_updater(session, updater)
                if result is None:
                    raise ImageNotFound(f"Image not found (id:{updater.pk_value})")
                return result.row.to_dataclass()
        except (ValueError, DBAPIError):
            raise ModifyImageActionValueError

    async def clear_image_resource_limits(
        self, image_canonical: str, architecture: str
    ) -> ImageData:
        async with self._db.begin_session() as session:
            image_row = await ImageRow.resolve(
                session, [ImageIdentifier(image_canonical, architecture)]
            )
            image_row._resources = {}
            data = image_row.to_dataclass()
        return data

    async def remove_tag_from_registry_with_validation(
        self, image_id: UUID, user_id: UUID
    ) -> ImageData:
        """
        Validates ownership and removes an image registry tag in a single database operation.
        Raises ForgetImageActionGenericForbiddenError if user doesn't own the image.
        """
        async with self._db.begin_readonly_session() as session:
            image_row = await self._validate_image_ownership(
                session, image_id, user_id, load_aliases=True
            )
            await image_row.untag_image_from_registry(self._db, session)
            data = image_row.to_dataclass()
        return data

    async def remove_image_and_aliases_with_validation(
        self, image_id: UUID, user_id: UUID
    ) -> ImageData:
        """
        Removes an image record and all its aliases from database after validating ownership.
        Raises ForgetImageActionGenericForbiddenError if user doesn't own the image.
        """

        try:
            async with self._db.begin_session() as session:
                image_row = await self._validate_image_ownership(
                    session, image_id, user_id, load_aliases=True
                )
                data = image_row.to_dataclass()
                for alias in image_row.aliases:
                    await session.delete(alias)
                await session.delete(image_row)
            return data
        except DBAPIError as e:
            raise PurgeImageActionByIdObjectDBError(str(e))
