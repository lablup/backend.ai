from ai.backend.manager.services.agent.processors import AgentProcessors
from ai.backend.manager.services.agent.service import AgentService
from ai.backend.manager.services.session.processors import SessionProcessors
from ai.backend.manager.services.session.service import SessionService
from ai.backend.manager.services.vfolder.processors import VFolderProcessors
from ai.backend.manager.services.vfolder.service import VFolderService


class Processors:
    session: SessionProcessors
    agent: AgentProcessors
    vfolder: VFolderProcessors

    def __init__(
        self,
        session_service: SessionService,
        agent_service: AgentService,
        vfolder_service: VFolderService,
    ) -> None:
        self.session = SessionProcessors(session_service)
        self.agent = AgentProcessors(agent_service)
        self.vfolder = VFolderProcessors(vfolder_service)
