import logging

import sqlalchemy as sa

from ai.backend.common.exception import UnknownImageReference
from ai.backend.common.types import ImageAlias
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.api.exceptions import ImageNotFound
from ai.backend.manager.models.image import ImageAliasRow, ImageIdentifier, ImageRow, ImageStatus
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.services.image.actions.alias_image import (
    AliasImageAction,
    AliasImageActionResult,
    AliasImageActionValueError,
)
from ai.backend.manager.services.image.actions.clear_images import (
    ClearImagesAction,
    ClearImagesActionResult,
    ClearImagesActionValueError,
)
from ai.backend.manager.services.image.actions.dealias_image import (
    DealiasImageAction,
    DealiasImageActionNoSuchAliasError,
    DealiasImageActionResult,
    DealiasImageActionValueError,
)
from ai.backend.manager.services.image.actions.forget_image import (
    ForgetImageAction,
    ForgetImageActionGenericForbiddenError,
    ForgetImageActionResult,
)
from ai.backend.manager.services.image.actions.forget_image_by_id import (
    ForgetImageActionByIdGenericForbiddenError,
    ForgetImageActionByIdObjectNotFoundError,
    ForgetImageByIdAction,
    ForgetImageByIdActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


class ImageService:
    _db: ExtendedAsyncSAEngine
    _agent_registry: AgentRegistry

    def __init__(self, db: ExtendedAsyncSAEngine, agent_registry: AgentRegistry) -> None:
        self._db = db
        self._agent_registry = agent_registry

    async def forget_image(self, action: ForgetImageAction) -> ForgetImageActionResult:
        async with self._db.begin_session() as session:
            image_row = await ImageRow.resolve(
                session,
                [
                    ImageIdentifier(action.reference, action.architecture),
                    ImageAlias(action.reference),
                ],
            )
            if action.client_role != UserRole.SUPERADMIN:
                if not image_row.is_customized_by(action.user_id):
                    raise ForgetImageActionGenericForbiddenError()
            await image_row.mark_as_deleted(session)
        return ForgetImageActionResult(image_row=image_row)

    async def forget_image_by_id(
        self, action: ForgetImageByIdAction
    ) -> ForgetImageByIdActionResult:
        async with self._db.begin_session() as session:
            image_row = await ImageRow.get(session, action.image_id, load_aliases=True)
            if not image_row:
                raise ForgetImageActionByIdObjectNotFoundError()
            if action.client_role != UserRole.SUPERADMIN:
                if not image_row.is_customized_by(action.user_id):
                    raise ForgetImageActionByIdGenericForbiddenError()
            await image_row.mark_as_deleted(session)
            return ForgetImageByIdActionResult(image_row=image_row)

    async def alias_image(self, action: AliasImageAction) -> AliasImageActionResult:
        try:
            async with self._db.begin_session() as session:
                try:
                    image_row = await ImageRow.resolve(
                        session, [ImageIdentifier(action.image_canonical, action.architecture)]
                    )
                except UnknownImageReference:
                    raise ImageNotFound
                else:
                    image_alias = ImageAliasRow(alias=action.alias, image_id=image_row.id)
                    image_row.aliases.append(image_alias)
        except ValueError:
            raise AliasImageActionValueError
        return AliasImageActionResult(image_alias=image_alias)

    async def dealias_image(self, action: DealiasImageAction) -> DealiasImageActionResult:
        try:
            async with self._db.begin_session() as session:
                existing_alias = await session.scalar(
                    sa.select(ImageAliasRow).where(ImageAliasRow.alias == action.alias),
                )
                if existing_alias is None:
                    raise DealiasImageActionNoSuchAliasError()
                await session.delete(existing_alias)
        except ValueError:
            raise DealiasImageActionValueError()
        return DealiasImageActionResult(image_alias=existing_alias)

    async def clear_images(self, action: ClearImagesAction) -> ClearImagesActionResult:
        try:
            async with self._db.begin_session() as session:
                await session.execute(
                    sa.update(ImageRow)
                    .where(ImageRow.registry == action.registry)
                    .where(ImageRow.status != ImageStatus.DELETED)
                    .values(status=ImageStatus.DELETED)
                )
        except ValueError:
            raise ClearImagesActionValueError()
        return ClearImagesActionResult()

    # async def purge_images(self, action: PurgeImagesAction) -> PurgeImagesActionResult:
    #     errors = []
    #     image_canonicals = [image.image_id() for image in action.images]
    #     arch_per_images = {image.name: image.architecture for image in action.images}
    #     reserved_bytes: int = 0
    #     responses: list[PurgeImageResponse] = []

    #     results = await self._agent_registry.purge_images(
    #         AgentId(action.agent_id), image_canonicals
    #     )

    #     for result in results.responses:
    #         image_canonical = result.image
    #         arch = arch_per_images[result.image]

    #         if not result.error:
    #             image_identifier = ImageIdentifier(image_canonical, arch)
    #             async with self._db.begin_session() as session:
    #                 image_row = await ImageRow.resolve(session, [image_identifier])
    #                 reserved_bytes += int(image_row.size_bytes)
    #                 responses.append(result)
    #         else:
    #             error_msg = f"Failed to purge images {image_canonical} from agent {action.agent_id}: {result.error}"
    #             log.error(error_msg)
    #             errors.append(error_msg)

    #     return PurgeImagesActionResult(
    #         reserved_bytes=reserved_bytes,
    #         results=responses,
    #     )
