import logging
from typing import Optional

import sqlalchemy as sa

from ai.backend.common.types import AgentId
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.agent.types import AgentData

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AgentDBSource:
    """ "Database source for agent-related operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_by_id(self, agent_id: AgentId) -> Optional[AgentData]:
        async with self._db.begin_readonly_session() as db_session:
            agent_row = await db_session.scalar(sa.select(AgentRow).where(AgentRow.id == agent_id))
            if agent_row is None:
                return None
            return AgentData.from_row(agent_row)
