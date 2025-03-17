from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.users.processors import UserProcessors
from ai.backend.manager.services.image.processors import ImageProcessors


class Processors:
    domain: DomainProcessors
    user: UserProcessors
    image: ImageProcessors

    def __init__(self, domain: DomainProcessors, user: UserProcessors, image: ImageProcessors) -> None:
        self.domain = domain
        self.user = user
        self.image = image
