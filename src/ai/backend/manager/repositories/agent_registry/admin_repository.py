from typing import Optional

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.types import AgentId, ResourceSlot
from ai.backend.manager.models.agent import AgentStatus, agents
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class AdminAgentRegistryRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_instance_force(self, inst_id: AgentId, field: Optional[str] = None):
        """
        Get agent instance by ID without permission validation.
        """
        async with self._db.begin_readonly() as conn:
            cols = [agents.c.id, agents.c.public_key]
            if field is not None:
                cols.append(field)
            query = sa.select(cols).select_from(agents).where(agents.c.id == inst_id)
            result = await conn.execute(query)
            return result.first()

    async def enumerate_instances_force(self, check_shadow: bool = True):
        """
        Enumerate all agent instances without permission validation.
        """
        async with self._db.begin_readonly() as conn:
            query = sa.select("*").select_from(agents)
            if check_shadow:
                query = query.where(agents.c.status == AgentStatus.ALIVE)
            async for row in await conn.stream(query):
                yield row

    async def update_instance_force(self, inst_id: AgentId, updated_fields: dict):
        """
        Update agent instance fields without permission validation.
        """
        async with self._db.begin_session() as conn:
            query = sa.update(agents).values(**updated_fields).where(agents.c.id == inst_id)
            await conn.execute(query)

    async def settle_agent_alloc_force(
        self,
        agent_id: AgentId,
        kernel_ids: list[str],
        new_occupied_slots: ResourceSlot,
        new_available_slots: ResourceSlot,
    ) -> None:
        """
        Force update agent resource allocation without validation.
        """
        async with self._db.begin_session() as session:
            agent_data = await self._get_agent_occupied_slots(session, agent_id)
            if agent_data is None:
                return

            current_occupied_slots = agent_data["occupied_slots"]
            current_available_slots = agent_data["available_slots"]

            updates = {}
            if current_occupied_slots != new_occupied_slots:
                updates["occupied_slots"] = new_occupied_slots
            if current_available_slots != new_available_slots:
                updates["available_slots"] = new_available_slots

            if updates:
                await self._update_agent_slots(session, agent_id, updates)

    async def mark_agent_terminated_force(
        self,
        agent_id: AgentId,
        status: AgentStatus,
        status_data: Optional[dict] = None,
    ) -> None:
        """
        Force mark agent as terminated without validation.
        """
        async with self._db.begin_session() as session:
            updates = {
                "status": status,
                "status_data": status_data or {},
            }
            await self._update_agent_slots(session, agent_id, updates)

    async def recalc_resource_usage_force(self, agent_ids: Optional[list[AgentId]] = None):
        """
        Force recalculate resource usage for agents without validation.
        """
        async with self._db.begin_session() as session:
            # Get all agents or specific agents
            if agent_ids:
                agent_query = sa.select(agents).where(agents.c.id.in_(agent_ids))
            else:
                agent_query = sa.select(agents)

            agent_result = await session.execute(agent_query)
            agent_rows = agent_result.fetchall()

            # Recalculate for each agent
            for agent_row in agent_rows:
                # Implementation would calculate actual resource usage
                # This is a simplified version
                updates = {
                    "occupied_slots": ResourceSlot(),  # Calculate actual occupied slots
                    "available_slots": agent_row.available_slots,  # Recalculate available slots
                }
                await self._update_agent_slots(session, agent_row.id, updates)

    async def _get_agent_occupied_slots(
        self, session: SASession, agent_id: AgentId
    ) -> Optional[dict]:
        """
        Private method to get agent occupied and available slots.
        """
        query = sa.select(agents.c.occupied_slots, agents.c.available_slots).where(
            agents.c.id == agent_id
        )
        result = await session.execute(query)
        row = result.first()
        return dict(row._mapping) if row else None

    async def _update_agent_slots(
        self, session: SASession, agent_id: AgentId, updates: dict
    ) -> None:
        """
        Private method to update agent slots using existing session.
        """
        query = sa.update(agents).values(**updates).where(agents.c.id == agent_id)
        await session.execute(query)
