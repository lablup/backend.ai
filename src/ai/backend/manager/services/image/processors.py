from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.services.image.actions.forget import (
    ForgetImageAction,
    ForgetImageActionResult,
)

from .service import ImageService


class ImageProcessors:
    forget_image: ActionProcessor[ForgetImageAction, ForgetImageActionResult]
    # forget_image_by_id: ActionProcessor[ForgetImageByIdAction, ForgetImageActionByIdResult]
    # purge_images: ActionProcessor[PurgeImagesAction, PurgeImagesActionResult]

    def __init__(self, service: ImageService) -> None:
        self.forget_image = ActionProcessor(service.forget_image)
        # self.forget_image_by_id = ActionProcessor(service.forget_image_by_id)
        # self.purge_images = ActionProcessor(service.purge_images)
