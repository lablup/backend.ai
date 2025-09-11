from typing import Optional

from ai.backend.common.metrics.metric import LayerType
from ai.backend.common.types import AgentId
from ai.backend.manager.decorators.repository_decorator import (
    create_layer_aware_repository_decorator,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.agent.db_source.db_source import AgentDBSource
from ai.backend.manager.services.agent.types import AgentData

# Layer-specific decorator for agent repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.AGENT)


class AgentRepository:
    _db_source: AgentDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = AgentDBSource(db)

    @repository_decorator()
    async def get_by_id(self, agent_id: AgentId) -> Optional[AgentData]:
        return await self._db_source.get_by_id(agent_id)
