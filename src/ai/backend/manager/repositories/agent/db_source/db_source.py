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
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.agent.types import AgentData

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AgentDBSource:
    """Database source for agent-related operations."""

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
            scaling_group_query = sa.select(ScalingGroupRow).where(
                ScalingGroupRow.name == upsert_data.metadata.scaling_group
            )
            scaling_group_result = (await conn.execute(scaling_group_query)).scalar()
            if scaling_group_result is None:
                log.error(
                    "Scaling group named [{}] does not exist.", upsert_data.metadata.scaling_group
                )
                raise ScalingGroupNotFound(upsert_data.metadata.scaling_group)

            query = (
                sa.select(AgentRow).where(AgentRow.id == upsert_data.metadata.id).with_for_update()
            )
            result = await conn.execute(query)
            row = result.first()
            upsert_result = UpsertResult.from_state_comparison(row, upsert_data)

            stmt = pg_insert(agents).values(upsert_data.insert_fields)
            final_query = stmt.on_conflict_do_update(
                index_elements=["id"], set_=upsert_data.update_fields
            )

            await conn.execute(final_query)

            return upsert_result
