from ai.backend.manager.services.session.processors import SessionProcessors
from ai.backend.manager.services.session.service import SessionService


class Processors:
    session: SessionProcessors

    def __init__(self, session_service: SessionService) -> None:
        self.session = SessionProcessors(session_service)
