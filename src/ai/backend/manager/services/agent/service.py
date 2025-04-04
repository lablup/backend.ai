import logging

import sqlalchemy as sa

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.services.agent.actions.sync_agent_registry import (
    SyncAgentRegistryAction,
    SyncAgentRegistryActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


class AgentService:
    _db: ExtendedAsyncSAEngine
    _agent_registry: AgentRegistry

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        agent_registry: AgentRegistry,
    ) -> None:
        self._db = db
        self._agent_registry = agent_registry

    async def sync_agent_registry(
        self, action: SyncAgentRegistryAction
    ) -> SyncAgentRegistryActionResult:
        agent_id = action.agent_id
        await self._agent_registry.sync_agent_kernel_registry(agent_id)
        async with self._db.begin_readonly_session() as db_session:
            agent_row = db_session.scalar(sa.select(AgentRow).where(AgentRow.id == agent_id))

        return SyncAgentRegistryActionResult(result=None, agent_row=agent_row)
