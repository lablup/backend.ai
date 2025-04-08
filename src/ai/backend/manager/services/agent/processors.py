from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.services.agent.actions.sync_agent_registry import (
    SyncAgentRegistryAction,
    SyncAgentRegistryActionResult,
)
from ai.backend.manager.services.agent.service import AgentService


class AgentProcessors:
    sync_agent_registry: ActionProcessor[SyncAgentRegistryAction, SyncAgentRegistryActionResult]

    def __init__(self, service: AgentService) -> None:
        self.sync_agent_registry = ActionProcessor(service.sync_agent_registry)
