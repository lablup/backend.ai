from ai.backend.manager.services.domain.processors import DomainProcessors


class Processors:
    domain: DomainProcessors

    def __init__(self, domain: DomainProcessors) -> None:
        self.domain = domain
