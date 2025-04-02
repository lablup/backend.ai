from ai.backend.manager.services.container_registry.processors import ContainerRegistryProcessors
from ai.backend.manager.services.container_registry.service import ContainerRegistryService
from ai.backend.manager.services.image.processors import ImageProcessors
from ai.backend.manager.services.image.service import ImageService


class Processors:
    image: ImageProcessors
    container_registry: ContainerRegistryProcessors

    def __init__(
        self, image_service: ImageService, container_registry_service: ContainerRegistryService
    ) -> None:
        self.image = ImageProcessors(image_service)
        self.container_registry = ContainerRegistryProcessors(container_registry_service)
