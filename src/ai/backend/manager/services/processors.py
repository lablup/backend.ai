from ai.backend.manager.services.agent.processors import AgentProcessors
from ai.backend.manager.services.agent.service import AgentService
from ai.backend.manager.services.session.processors import SessionProcessors
from ai.backend.manager.services.session.service import SessionService


class Processors:
    session: SessionProcessors
    agent: AgentProcessors

    def __init__(self, session_service: SessionService, agent_service: AgentService) -> None:
        self.session = SessionProcessors(session_service)
        self.agent = AgentProcessors(agent_service)
