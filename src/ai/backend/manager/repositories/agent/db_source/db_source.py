import logging
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ai.backend.common.types import AgentId
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.agent.types import (
    AgentHeartbeatUpsert,
    UpsertResult,
)
from ai.backend.manager.errors.resource import ScalingGroupNotFound
from ai.backend.manager.models import agents
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

    async def upsert_agent_with_state(self, upsert_data: AgentHeartbeatUpsert) -> UpsertResult:
        async with self._db.begin() as conn:
            query = sa.select(AgentRow).where(AgentRow.id == upsert_data.id).with_for_update()
            result = await conn.execute(query)
            row = result.first()
            upsert_result = UpsertResult.from_state_comparison(row, upsert_data)

            stmt = pg_insert(agents).values(upsert_data.insert_fields)
            final_query = stmt.on_conflict_do_update(
                index_elements=["id"], set_=upsert_data.update_fields
            )
            try:
                await conn.execute(final_query)
            except sa.exc.IntegrityError:
                log.error("Scaling group named [{}] does not exist.", upsert_data.scaling_group)
                raise ScalingGroupNotFound(upsert_data.scaling_group)

            return upsert_result
