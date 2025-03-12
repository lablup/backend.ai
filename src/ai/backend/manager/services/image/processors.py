from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.services.image.actions import (
    CreateImageAction,
    CreateImageActionResult,
    ForgetImageAction,
    ForgetImageActionResult,
    PurgeImageAction,
    PurgeImageActionResult,
)

from .service import ImageService


class ImageProcessors:
    create: ActionProcessor[CreateImageAction, CreateImageActionResult]
    forget: ActionProcessor[ForgetImageAction, ForgetImageActionResult]
    purge: ActionProcessor[PurgeImageAction, PurgeImageActionResult]

    def __init__(self, service: ImageService) -> None:
        self.create = ActionProcessor(service.create_image)
        self.forget = ActionProcessor(service.forget_image)
        self.purge = ActionProcessor(service.purge_image)
