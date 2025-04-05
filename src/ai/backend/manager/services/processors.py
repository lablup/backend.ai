from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.users.processors import UserProcessors


class Processors:
    domain: DomainProcessors
    user: UserProcessors

    def __init__(self, domain: DomainProcessors, user: UserProcessors) -> None:
        self.domain = domain
        self.user = user
