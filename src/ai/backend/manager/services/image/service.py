import logging

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.api.exceptions import ObjectNotFound
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.image.actions import (
    ForgetImageAction,
    ForgetImageActionResult,
)

log = BraceStyleAdapter(logging.getLogger("ai.backend.accelerator.cuda"))


class ImageService:
    _db: ExtendedAsyncSAEngine

    def __init__(self): ...

    async def forget_image(self, action: ForgetImageAction) -> ForgetImageActionResult:
        client_role = action.client_role

        async with self._db.begin_session() as session:
            image_row = await ImageRow.get(session, action.image_uuid, load_aliases=True)
            if not image_row:
                raise ObjectNotFound("image")
            if client_role != UserRole.SUPERADMIN:
                # if not image_row.is_customized_by(ctx.user["uuid"]):
                pass
                # raise Forbidden("user role is not allowed to forget the image")
                # return ForgetImageById(ok=False, msg="Forbidden")
            await image_row.mark_as_deleted(session)
        return ForgetImageActionResult()

    # async def purge_images(self, action: PurgeImagesAction) -> PurgeImagesActionResult:
    #     errors = []
    #     task_result = PurgeImagesResult(results=PurgeImageResponses([]), reserved_bytes=0)
    #     arch_per_images = {image.name: image.architecture for image in images}

    #     results = await ctx.registry.purge_images(AgentId(action.agent_id), image_canonicals)

    #     for result in results.responses:
    #         image_canonical = result.image
    #         arch = arch_per_images[result.image]

    #         if not result.error:
    #             image_identifier = ImageIdentifier(image_canonical, arch)
    #             async with ctx.db.begin_session() as session:
    #                 image_row = await ImageRow.resolve(session, [image_identifier])
    #                 task_result.reserved_bytes += image_row.size_bytes
    #                 task_result.results.responses.append(result)

    #         else:
    #             error_msg = (
    #                 f"Failed to purge image {image_canonical} from agent {agent_id}: {result.error}"
    #             )
    #             log.error(error_msg)
    #             errors.append(error_msg)
