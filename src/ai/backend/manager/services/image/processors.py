from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.services.image.actions.alias_image import (
    AliasImageAction,
    AliasImageActionResult,
)
from ai.backend.manager.services.image.actions.clear_images import (
    ClearImagesAction,
    ClearImagesActionResult,
)
from ai.backend.manager.services.image.actions.dealias_image import (
    DealiasImageAction,
    DealiasImageActionResult,
)
from ai.backend.manager.services.image.actions.forget_image import (
    ForgetImageAction,
    ForgetImageActionResult,
)
from ai.backend.manager.services.image.actions.forget_image_by_id import (
    ForgetImageByIdAction,
    ForgetImageByIdActionResult,
)

from .service import ImageService


class ImageProcessors:
    forget_image: ActionProcessor[ForgetImageAction, ForgetImageActionResult]
    forget_image_by_id: ActionProcessor[ForgetImageByIdAction, ForgetImageByIdActionResult]
    alias_image: ActionProcessor[AliasImageAction, AliasImageActionResult]
    dealias_image: ActionProcessor[DealiasImageAction, DealiasImageActionResult]
    clear_images: ActionProcessor[ClearImagesAction, ClearImagesActionResult]

    # TODO: Batch action 지원 추가 필요
    # purge_images: ActionProcessor[PurgeImagesAction, PurgeImagesActionResult]

    # purge_image_by_id: ActionProcessor[PurgeImagesAction, PurgeImagesActionResult]

    def __init__(self, service: ImageService) -> None:
        self.forget_image = ActionProcessor(service.forget_image)
        self.forget_image_by_id = ActionProcessor(service.forget_image_by_id)
        self.alias_image = ActionProcessor(service.alias_image)
        self.dealias_image = ActionProcessor(service.dealias_image)
        self.clear_images = ActionProcessor(service.clear_images)

        # self.purge_images = ActionProcessor(service.purge_images)
        # self.purge_image_by_id = ActionProcessor(service.purge_images)
