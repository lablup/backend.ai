from ai.backend.manager.services.container_registry.processors import ContainerRegistryProcessors
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.users.processors import UserProcessors
from ai.backend.manager.services.image.processors import ImageProcessors


class Processors:
    domain: DomainProcessors
    user: UserProcessors
    image: ImageProcessors
    container_registry: ContainerRegistryProcessors

    def __init__(
        self,
        domain: DomainProcessors,
        user: UserProcessors,
        image: ImageProcessors,
        container_registry: ContainerRegistryProcessors,
    ) -> None:
        self.domain = domain
        self.user = user
        self.image = image
        self.container_registry = container_registry
