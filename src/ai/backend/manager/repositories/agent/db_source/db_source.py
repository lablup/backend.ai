import logging
from typing import TYPE_CHECKING, Optional

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ai.backend.common.types import AgentId
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.agent.types import (
    AgentData,
    AgentHeartbeatUpsert,
    UpsertResult,
)
from ai.backend.manager.errors.resource import ScalingGroupNotFound
from ai.backend.manager.models import agents
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class AgentDBSource:
    """Database source for agent-related operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_by_id(self, agent_id: AgentId) -> Optional[AgentData]:
        async with self._db.begin_readonly_session() as db_session:
            agent_row: Optional[AgentRow] = await db_session.scalar(
                sa.select(AgentRow).where(AgentRow.id == agent_id)
            )
            if agent_row is None:
                return None
            return agent_row.to_data()

    async def _check_scaling_group_exists(
        self, session: "AsyncSession", scaling_group_name: str
    ) -> None:
        scaling_group_row = await session.scalar(
            sa.select(ScalingGroupRow).where(ScalingGroupRow.name == scaling_group_name)
        )
        if not scaling_group_row:
            log.error("Scaling group named [{}] does not exist.", scaling_group_name)
            raise ScalingGroupNotFound(scaling_group_name)

    async def upsert_agent_with_state(self, upsert_data: AgentHeartbeatUpsert) -> UpsertResult:
        async with self._db.begin_session() as session:
            await self._check_scaling_group_exists(session, upsert_data.metadata.scaling_group)

            query = (
                sa.select(AgentRow).where(AgentRow.id == upsert_data.metadata.id).with_for_update()
            )
            row: Optional[AgentRow] = await session.scalar(query)
            agent_data = row.to_data() if row is not None else None
            upsert_result = UpsertResult.from_state_comparison(agent_data, upsert_data)

            stmt = pg_insert(agents).values(upsert_data.insert_fields)
            final_query = stmt.on_conflict_do_update(
                index_elements=["id"], set_=upsert_data.update_fields
            )

            await session.execute(final_query)

            return upsert_result
