from ai.backend.manager.services.resource.processors import ResourceProcessors
from ai.backend.manager.services.resource.service import ResourceService


class Processors:
    resource: ResourceProcessors

    def __init__(self, resource_service: ResourceService) -> None:
        self.resource = ResourceProcessors(resource_service)
