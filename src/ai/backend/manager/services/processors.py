from ai.backend.manager.services.users.processors import UserProcessors


class Processors:
    user: UserProcessors

    def __init__(self, user_processor: UserProcessors) -> None:
        self.user = user_processor
