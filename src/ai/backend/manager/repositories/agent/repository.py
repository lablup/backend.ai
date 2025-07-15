import sqlalchemy as sa

from ai.backend.common.decorators import create_layer_aware_repository_decorator
from ai.backend.common.metrics.metric import LayerType
from ai.backend.common.types import AgentId
from ai.backend.manager.errors.agent import AgentNotFound
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, SASession
from ai.backend.manager.services.agent.types import AgentData

# Layer-specific decorator for agent repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.AGENT)


class AgentRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def _get_agent_by_id(self, session: SASession, agent_id: AgentId) -> AgentRow:
        """Private method to get an agent by ID using an existing session.
        Raises AgentNotFound if not found."""
        agent_row = await session.scalar(sa.select(AgentRow).where(AgentRow.id == agent_id))
        if agent_row is None:
            raise AgentNotFound()
        return agent_row

    @repository_decorator()
    async def get_by_id(self, agent_id: AgentId) -> AgentData:
        async with self._db.begin_readonly_session() as db_session:
            agent_row = await self._get_agent_by_id(db_session, agent_id)
            return AgentData.from_row(agent_row)
