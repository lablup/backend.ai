from uuid import UUID

from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.docker import ImageRef
from ai.backend.common.types import ImageAlias
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.errors.image import (
    ImageNotFound,
    PurgeImageActionByIdObjectDBError,
)
from ai.backend.manager.models.image import (
    ImageIdentifier,
    ImageRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class AdminImageRepository:
    """
    Repository for admin-specific image operations that bypass ownership checks.
    This should only be used by superadmin users.
    """

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def _resolve_image(
        self,
        session: SASession,
        identifiers: list[ImageAlias | ImageRef | ImageIdentifier],
    ) -> ImageRow:
        return await ImageRow.resolve(session, identifiers)

    async def _get_image_by_id(
        self, session: SASession, image_id: UUID, load_aliases: bool = False
    ) -> ImageRow:
        image_row = await ImageRow.get(session, image_id, load_aliases=load_aliases)
        if not image_row:
            raise ImageNotFound()
        return image_row

    async def soft_delete_image_force(
        self, identifiers: list[ImageAlias | ImageRef | ImageIdentifier]
    ) -> ImageData:
        """
        Marks an image as deleted without checking ownership.
        This is a forceful deletion and should be used with caution.
        """
        async with self._db.begin_session() as session:
            row = await self._resolve_image(session, identifiers)
            await row.mark_as_deleted(session)
            data = row.to_dataclass()
        return data

    async def soft_delete_image_by_id_force(self, image_id: UUID) -> ImageData:
        """
        Marks an image as deleted by its ID without checking ownership.
        This is a forceful deletion and should be used with caution.
        """
        async with self._db.begin_session() as session:
            image_row = await self._get_image_by_id(session, image_id)
            await image_row.mark_as_deleted(session)
            data = image_row.to_dataclass()
        return data

    async def delete_image_with_aliases_force(self, image_id: UUID) -> ImageData:
        """
        Deletes an image and all its aliases without checking ownership.
        This is a forceful deletion and should be used with caution.
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
            raise PurgeImageActionByIdObjectDBError(str(e))

    async def untag_image_from_registry_force(self, image_id: UUID) -> ImageData:
        """
        Untags an image from registry without ownership check.
        This is an admin-only operation.
        """
        async with self._db.begin_readonly_session() as session:
            image_row = await self._get_image_by_id(session, image_id, load_aliases=True)
            await image_row.untag_image_from_registry(self._db, session)
            data = image_row.to_dataclass()
        return data
