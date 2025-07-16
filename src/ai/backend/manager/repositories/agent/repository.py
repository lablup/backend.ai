from typing import Optional

import sqlalchemy as sa

from ai.backend.common.metrics.metric import LayerType
from ai.backend.common.types import AgentId
from ai.backend.manager.decorators.repository_decorator import (
    create_layer_aware_repository_decorator,
)
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.agent.types import AgentData

# Layer-specific decorator for agent repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.AGENT)


class AgentRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @repository_decorator()
    async def get_by_id(self, agent_id: AgentId) -> Optional[AgentData]:
        async with self._db.begin_readonly_session() as db_session:
            agent_row = await db_session.scalar(sa.select(AgentRow).where(AgentRow.id == agent_id))
            if agent_row is None:
                return None
            return AgentData.from_row(agent_row)
