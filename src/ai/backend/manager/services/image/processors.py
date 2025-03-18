from ai.backend.manager.actions.processor import ActionProcessor
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

    # TODO: Batch action 지원 추가 필요
    # purge_images: ActionProcessor[PurgeImagesAction, PurgeImagesActionResult]

    # purge_image_by_id: ActionProcessor[PurgeImagesAction, PurgeImagesActionResult]

    def __init__(self, service: ImageService) -> None:
        self.forget_image = ActionProcessor(service.forget_image)
        # self.forget_image_by_id = ActionProcessor(service.forget_image_by_id)
        # self.purge_images = ActionProcessor(service.purge_images)
        # self.purge_image_by_id = ActionProcessor(service.purge_images)
