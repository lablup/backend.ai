from typing import Optional, cast
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.docker import ImageRef
from ai.backend.common.metrics.metric import LayerType
from ai.backend.common.types import ImageAlias
from ai.backend.manager.data.image.types import ImageAliasData, ImageData, RescanImagesResult
from ai.backend.manager.decorators.repository_decorator import (
    create_layer_aware_repository_decorator,
)
from ai.backend.manager.errors.image import (
    AliasImageActionDBError,
    AliasImageActionValueError,
    ForgetImageForbiddenError,
    ForgetImageNotFoundError,
    ImageAliasNotFound,
    ModifyImageActionValueError,
)
from ai.backend.manager.models.image import (
    ImageAliasRow,
    ImageIdentifier,
    ImageRow,
    scan_single_image,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

# Layer-specific decorator for image repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.IMAGE)


class ImageRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @repository_decorator()
    async def resolve_image(
        self, identifiers: list[ImageAlias | ImageRef | ImageIdentifier]
    ) -> ImageData:
        """
        Resolves an image by its identifiers, which can be a combination of
        ImageAlias, ImageRef, or ImageIdentifier.
        Returns an ImageData object.
        Raises Exception if the image cannot be resolved.
        """
        async with self._db.begin_session() as session:
            row = await self._resolve_image(session, identifiers)
            data = row.to_dataclass()
        return data

    @repository_decorator()
    async def resolve_images_batch(
        self, identifier_lists: list[list[ImageIdentifier]]
    ) -> list[ImageData]:
        """
        Resolves multiple images by their identifiers in a single database session.
        Returns a list of ImageData objects.
        More efficient than multiple individual resolve_image calls.
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
        self, session: SASession, image_id: UUID, load_aliases: bool = False
    ) -> Optional[ImageRow]:
        """
        Private method to get an image by ID using an existing session.
        Returns None if image is not found.
        """
        return await ImageRow.get(session, image_id, load_aliases=load_aliases)

    async def _validate_image_ownership(
        self, session: SASession, image_id: UUID, user_id: UUID, load_aliases: bool = False
    ) -> ImageRow:
        """
        Private method to get an image and validate ownership using an existing session.
        Raises ForgetImageActionGenericForbiddenError if image doesn't exist or user doesn't own it.
        """
        image_row = await self._get_image_by_id(session, image_id, load_aliases)
        if not image_row:
            raise ForgetImageNotFoundError()
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

    @repository_decorator()
    async def get_image_by_id(
        self, image_id: UUID, load_aliases: bool = False
    ) -> Optional[ImageData]:
        async with self._db.begin_session() as session:
            row = await self._get_image_by_id(session, image_id, load_aliases)
            if not row:
                return None
            data = row.to_dataclass()
        return data

    @repository_decorator()
    async def soft_delete_user_image(
        self,
        identifiers: list[ImageAlias | ImageRef | ImageIdentifier],
        user_id: UUID,
    ) -> ImageData:
        """
        Marks an image as deleted for a specific user.
        Raises ForgetImageActionGenericForbiddenError if the user does not own the image.
        """
        async with self._db.begin_session() as session:
            row = await self._resolve_image(session, identifiers)
            if not row.is_owned_by(user_id):
                raise ForgetImageForbiddenError()
            await row.mark_as_deleted(session)
            data = row.to_dataclass()
        return data

    @repository_decorator()
    async def soft_delete_image_by_id(
        self,
        image_id: UUID,
        user_id: UUID,
    ) -> ImageData:
        """
        Marks an image as deleted by its ID.
        Validates ownership by user_id before deletion.
        Raises ForgetImageActionGenericForbiddenError if the user does not own the image.
        """
        async with self._db.begin_session() as session:
            image_row = await self._validate_image_ownership(session, image_id, user_id)
            await image_row.mark_as_deleted(session)
            data = image_row.to_dataclass()
        return data

    @repository_decorator()
    async def get_and_validate_image_ownership(
        self, image_id: UUID, user_id: UUID, load_aliases: bool = False
    ) -> ImageData:
        """
        Gets an image by ID and validates ownership in a single operation.
        Raises ForgetImageActionGenericForbiddenError if image doesn't exist or user doesn't own it.
        """
        async with self._db.begin_session() as session:
            image_row = await self._validate_image_ownership(
                session, image_id, user_id, load_aliases
            )
            data = image_row.to_dataclass()
        return data

    @repository_decorator()
    async def add_image_alias(
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

    @repository_decorator()
    async def get_image_alias(self, alias: str) -> ImageAliasData:
        async with self._db.begin_session() as session:
            row = await self._get_image_alias_by_name(session, alias)
            data = ImageAliasData(id=row.id, alias=row.alias)
        return data

    @repository_decorator()
    async def delete_image_alias(self, alias: str) -> tuple[UUID, ImageAliasData]:
        async with self._db.begin_session() as session:
            existing_alias = await self._get_image_alias_by_name(session, alias)
            image_id = existing_alias.image_id
            alias_data = ImageAliasData(id=existing_alias.id, alias=existing_alias.alias)
            await session.delete(existing_alias)
        return image_id, alias_data

    @repository_decorator()
    async def scan_image_by_identifier(
        self, image_canonical: str, architecture: str
    ) -> RescanImagesResult:
        """
        Scans a single image by resolving it first and then scanning.
        Returns RescanImagesResult with the scanned image data.
        """
        from ai.backend.manager.models.container_registry import ContainerRegistryRow

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
                raise ValueError(f"Registry not found for image {image_canonical}")

            # Call the original scan function
            result = await scan_single_image(self._db, registry_key, registry_row, image_canonical)

        return result

    @repository_decorator()
    async def untag_image_from_registry(self, image_id: UUID) -> Optional[ImageData]:
        async with self._db.begin_readonly_session() as session:
            image_row = await self._get_image_by_id(session, image_id, load_aliases=True)
            if not image_row:
                return None
            await image_row.untag_image_from_registry(self._db, session)
            data = image_row.to_dataclass()
        return data

    @repository_decorator()
    async def update_image_properties(
        self, target: str, architecture: str, properties_to_update: dict
    ) -> ImageData:
        try:
            async with self._db.begin_session() as session:
                image_row = await ImageRow.resolve(
                    session,
                    [
                        ImageIdentifier(target, architecture),
                        ImageAlias(target),
                    ],
                )
                for key, value in properties_to_update.items():
                    setattr(image_row, key, value)
                data = image_row.to_dataclass()
            return data
        except (ValueError, DBAPIError):
            raise ModifyImageActionValueError

    @repository_decorator()
    async def clear_image_custom_resource_limit(
        self, image_canonical: str, architecture: str
    ) -> ImageData:
        async with self._db.begin_session() as session:
            image_row = await ImageRow.resolve(
                session, [ImageIdentifier(image_canonical, architecture)]
            )
            image_row._resources = {}
            data = image_row.to_dataclass()
        return data

    @repository_decorator()
    async def untag_image_from_registry_validated(self, image_id: UUID, user_id: UUID) -> ImageData:
        """
        Validates ownership and untags an image from registry in a single operation.
        Raises ForgetImageActionGenericForbiddenError if user doesn't own the image.
        """
        async with self._db.begin_readonly_session() as session:
            image_row = await self._validate_image_ownership(
                session, image_id, user_id, load_aliases=True
            )
            await image_row.untag_image_from_registry(self._db, session)
            data = image_row.to_dataclass()
        return data

    @repository_decorator()
    async def delete_image_with_aliases_validated(self, image_id: UUID, user_id: UUID) -> ImageData:
        """
        Deletes an image and all its aliases after validating ownership.
        Raises ForgetImageActionGenericForbiddenError if user doesn't own the image.
        """
        from ai.backend.manager.errors.image import PurgeImageActionByIdObjectDBError

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
