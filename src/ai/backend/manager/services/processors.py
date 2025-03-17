from ai.backend.manager.services.image.processors import ImageProcessors
from ai.backend.manager.services.image.service import ImageService


class Processors:
    image: ImageProcessors

    def __init__(self, image_service: ImageService) -> None:
        self.image = ImageProcessors(image_service)
