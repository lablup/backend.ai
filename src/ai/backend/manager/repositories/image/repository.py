from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.docker import ImageRef
from ai.backend.common.types import ImageAlias
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.errors.exceptions import ForgetImageActionGenericForbiddenError
from ai.backend.manager.models.image import (
    ImageAliasRow,
    ImageIdentifier,
    ImageRow,
    scan_single_image,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.image.actions.alias_image import (
    AliasImageActionDBError,
    AliasImageActionValueError,
)
from ai.backend.manager.services.image.actions.modify_image import (
    ModifyImageActionValueError,
)
from ai.backend.manager.services.image.actions.purge_image_by_id import (
    PurgeImageActionByIdObjectDBError,
)


class ImageRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

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
            return row.to_dataclass()

    async def _resolve_image(
        self,
        session: SASession,
        identifiers: list[ImageAlias | ImageRef | ImageIdentifier],
    ) -> ImageRow:
        return await ImageRow.resolve(session, identifiers)

    async def get_image_by_id(self, image_id: UUID, load_aliases: bool = False) -> ImageRow | None:
        async with self._db.begin_session() as session:
            return await ImageRow.get(session, image_id, load_aliases=load_aliases)

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
                raise ForgetImageActionGenericForbiddenError()
            await row.mark_as_deleted(session)
            return row.to_dataclass()

    async def soft_delete_image_force(
        self, identifiers: list[ImageAlias | ImageRef | ImageIdentifier]
    ) -> ImageData:
        """
        Marks an image as deleted without checking ownership.
        This is a forceful deletion and should be used with caution.
        """
        # TODO: Separate these methods from ImageRepository for security and clarity. Make a AdminImageRepository.
        async with self._db.begin_session() as session:
            row = await self._resolve_image(session, identifiers)
            await row.mark_as_deleted(session)
            return row.to_dataclass()

    async def soft_delete_image_by_id(
        self, image_id: UUID, user_id: UUID | None = None
    ) -> ImageData:
        """
        Marks an image as deleted by its ID.
        If user_id is provided, checks if the user owns the image.
        Raises ForgetImageActionGenericForbiddenError if the user does not own the image.
        """
        async with self._db.begin_session() as session:
            image_row = await ImageRow.get(session, image_id)
            if not image_row:
                raise ForgetImageActionGenericForbiddenError()
            if user_id and not image_row.is_owned_by(user_id):
                raise ForgetImageActionGenericForbiddenError()
            await image_row.mark_as_deleted(session)
            return image_row.to_dataclass()

    async def mark_image_as_deleted(self, image_id: UUID) -> None:
        async with self._db.begin_session() as session:
            image_row = await ImageRow.get(session, image_id)
            if image_row:
                await image_row.mark_as_deleted(session)
            if not image_row.is_owned_by(action.user_id):
                raise ForgetImageActionGenericForbiddenError()

    async def add_image_alias(
        self, alias: str, image_canonical: str, architecture: str
    ) -> tuple[UUID, ImageAliasRow]:
        try:
            async with self._db.begin_session() as session:
                image_row = await ImageRow.resolve(
                    session, [ImageIdentifier(image_canonical, architecture)]
                )
                image_alias = ImageAliasRow(alias=alias, image_id=image_row.id)
                image_row.aliases.append(image_alias)
                return image_row.id, image_alias
        except ValueError:
            raise AliasImageActionValueError
        except sa.exc.DBAPIError as e:
            raise AliasImageActionDBError(e)

    async def get_image_alias(self, alias: str) -> ImageAliasRow | None:
        async with self._db.begin_session() as session:
            return await session.scalar(
                sa.select(ImageAliasRow).where(ImageAliasRow.alias == alias),
            )

    async def delete_image_alias(self, alias: str) -> ImageAliasRow | None:
        async with self._db.begin_session() as session:
            existing_alias = await session.scalar(
                sa.select(ImageAliasRow).where(ImageAliasRow.alias == alias),
            )
            if existing_alias is not None:
                await session.delete(existing_alias)
            return existing_alias

    async def delete_image_with_aliases(self, image_id: UUID) -> ImageRow | None:
        try:
            async with self._db.begin_session() as session:
                image_row = await ImageRow.get(session, image_id, load_aliases=True)
                if image_row:
                    for alias in image_row.aliases:
                        await session.delete(alias)
                    await session.delete(image_row)
                return image_row
        except sa.exc.DBAPIError as e:
            raise PurgeImageActionByIdObjectDBError(e)

    async def scan_single_image(self, registry_key: str, image_row: ImageRow, image_canonical: str):
        async with self._db.begin_session() as session:
            return await scan_single_image(session, registry_key, image_row, image_canonical)

    async def untag_image_from_registry(self, image_id: UUID) -> ImageRow | None:
        async with self._db.begin_readonly_session() as session:
            image_row = await ImageRow.get(session, image_id, load_aliases=True)
            if image_row:
                await image_row.untag_image_from_registry(self._db, session)
            return image_row

    async def update_image_properties(
        self, target: str, architecture: str, properties_to_update: dict
    ) -> ImageRow:
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
                return image_row
        except (ValueError, sa.exc.DBAPIError):
            raise ModifyImageActionValueError

    async def clear_image_custom_resource_limit(
        self, image_canonical: str, architecture: str
    ) -> ImageRow:
        async with self._db.begin_session() as session:
            image_row = await ImageRow.resolve(
                session, [ImageIdentifier(image_canonical, architecture)]
            )
            image_row._resources = {}
            await session.flush()
            return image_row
