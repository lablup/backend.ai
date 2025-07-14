from typing import Optional

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.types import AccessKey, AgentId, ResourceSlot
from ai.backend.manager.models.agent import AgentStatus, agents
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class AgentRegistryRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_instance(self, inst_id: AgentId, field=None):
        """
        Get agent instance by ID.
        """
        async with self._db.begin_readonly() as conn:
            cols = [agents.c.id, agents.c.public_key]
            if field is not None:
                cols.append(field)
            query = sa.select(cols).select_from(agents).where(agents.c.id == inst_id)
            result = await conn.execute(query)
            return result.first()

    async def enumerate_instances(self, check_shadow: bool = True):
        """
        Enumerate all agent instances.
        """
        async with self._db.begin_readonly() as conn:
            query = sa.select("*").select_from(agents)
            if check_shadow:
                query = query.where(agents.c.status == AgentStatus.ALIVE)
            async for row in await conn.stream(query):
                yield row

    async def update_instance(self, inst_id: AgentId, updated_fields: dict):
        """
        Update agent instance fields.
        """
        async with self._db.begin() as conn:
            query = sa.update(agents).values(**updated_fields).where(agents.c.id == inst_id)
            await conn.execute(query)

    async def settle_agent_alloc(
        self,
        agent_id: AgentId,
        kernel_ids: list[str],
        new_occupied_slots: ResourceSlot,
        new_available_slots: ResourceSlot,
    ) -> None:
        """
        Update agent resource allocation after settling resources.
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

    async def handle_heartbeat(
        self,
        agent_id: AgentId,
        agent_info: dict,
        check_scaling_group: bool = True,
    ) -> bool:
        """
        Handle agent heartbeat and update agent status.
        Returns True if the agent was created or updated successfully.
        """
        async with self._db.begin_session() as session:
            # Try to get existing agent
            existing_agent = await self._get_agent_by_id(session, agent_id)

            if existing_agent is None:
                # Insert new agent
                await self._insert_agent(session, agent_id, agent_info)
                return True
            else:
                # Update existing agent
                await self._update_agent_heartbeat(session, agent_id, agent_info)
                return True

    async def mark_agent_terminated(
        self,
        agent_id: AgentId,
        status: AgentStatus,
        status_data: Optional[dict] = None,
    ) -> None:
        """
        Mark agent as terminated with given status.
        """
        async with self._db.begin_session() as session:
            updates = {
                "status": status,
                "status_data": status_data or {},
            }
            await self._update_agent_slots(session, agent_id, updates)

    async def _get_agent_by_id(self, session: SASession, agent_id: AgentId) -> Optional[dict]:
        """
        Private method to get agent by ID using existing session.
        """
        query = sa.select(agents).where(agents.c.id == agent_id)
        result = await session.execute(query)
        row = result.first()
        return dict(row._mapping) if row else None

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

    async def _insert_agent(self, session: SASession, agent_id: AgentId, agent_info: dict) -> None:
        """
        Private method to insert new agent using existing session.
        """
        insert_data = {"id": agent_id, "status": AgentStatus.ALIVE, **agent_info}
        query = sa.insert(agents).values(**insert_data)
        await session.execute(query)

    async def _update_agent_heartbeat(
        self, session: SASession, agent_id: AgentId, agent_info: dict
    ) -> None:
        """
        Private method to update agent heartbeat data using existing session.
        """
        updates = {"status": AgentStatus.ALIVE, **agent_info}
        query = sa.update(agents).values(**updates).where(agents.c.id == agent_id)
        await session.execute(query)

    async def get_user_occupancy(self, user_id, db_sess=None) -> ResourceSlot:
        """
        Get total resource occupation by user.
        """

        if db_sess is None:
            async with self._db.begin_readonly_session() as session:
                return await self._get_user_occupancy(session, user_id)
        else:
            return await self._get_user_occupancy(db_sess, user_id)

    async def _get_user_occupancy(self, session: SASession, user_id) -> ResourceSlot:
        """
        Private method to get user resource occupancy.
        """
        from ai.backend.manager.models import USER_RESOURCE_OCCUPYING_KERNEL_STATUSES

        query = sa.select(KernelRow.occupied_slots).where(
            (KernelRow.user_uuid == user_id)
            & (KernelRow.status.in_(USER_RESOURCE_OCCUPYING_KERNEL_STATUSES))
        )
        result = await session.execute(query)
        rows = result.fetchall()

        occupied_slots = ResourceSlot()
        for row in rows:
            occupied_slots += row.occupied_slots
        return occupied_slots

    async def get_keypair_occupancy(self, access_key: AccessKey, db_sess=None) -> ResourceSlot:
        """
        Get total resource occupation by access key.
        """

        if db_sess is None:
            async with self._db.begin_readonly_session() as session:
                return await self._get_keypair_occupancy(session, access_key)
        else:
            return await self._get_keypair_occupancy(db_sess, access_key)

    async def _get_keypair_occupancy(
        self, session: SASession, access_key: AccessKey
    ) -> ResourceSlot:
        """
        Private method to get keypair resource occupancy.
        """
        from ai.backend.manager.models import USER_RESOURCE_OCCUPYING_KERNEL_STATUSES

        query = sa.select(KernelRow.occupied_slots).where(
            (KernelRow.access_key == access_key)
            & (KernelRow.status.in_(USER_RESOURCE_OCCUPYING_KERNEL_STATUSES))
        )
        result = await session.execute(query)
        rows = result.fetchall()

        occupied_slots = ResourceSlot()
        for row in rows:
            occupied_slots += row.occupied_slots
        return occupied_slots

    async def get_domain_occupancy(self, domain_name: str, db_sess=None) -> ResourceSlot:
        """
        Get total resource occupation by domain.
        """

        if db_sess is None:
            async with self._db.begin_readonly_session() as session:
                return await self._get_domain_occupancy(session, domain_name)
        else:
            return await self._get_domain_occupancy(db_sess, domain_name)

    async def _get_domain_occupancy(self, session: SASession, domain_name: str) -> ResourceSlot:
        """
        Private method to get domain resource occupancy.
        """
        from ai.backend.manager.models import USER_RESOURCE_OCCUPYING_KERNEL_STATUSES

        query = sa.select(KernelRow.occupied_slots).where(
            (KernelRow.domain_name == domain_name)
            & (KernelRow.status.in_(USER_RESOURCE_OCCUPYING_KERNEL_STATUSES))
        )
        result = await session.execute(query)
        rows = result.fetchall()

        occupied_slots = ResourceSlot()
        for row in rows:
            occupied_slots += row.occupied_slots
        return occupied_slots

    async def get_group_occupancy(self, group_id, db_sess=None) -> ResourceSlot:
        """
        Get total resource occupation by group.
        """

        if db_sess is None:
            async with self._db.begin_readonly_session() as session:
                return await self._get_group_occupancy(session, group_id)
        else:
            return await self._get_group_occupancy(db_sess, group_id)

    async def _get_group_occupancy(self, session: SASession, group_id) -> ResourceSlot:
        """
        Private method to get group resource occupancy.
        """
        from ai.backend.manager.models import USER_RESOURCE_OCCUPYING_KERNEL_STATUSES

        query = sa.select(KernelRow.occupied_slots).where(
            (KernelRow.group_id == group_id)
            & (KernelRow.status.in_(USER_RESOURCE_OCCUPYING_KERNEL_STATUSES))
        )
        result = await session.execute(query)
        rows = result.fetchall()

        occupied_slots = ResourceSlot()
        for row in rows:
            occupied_slots += row.occupied_slots
        return occupied_slots

    async def update_agent_resource_allocation(
        self, agent_id: AgentId, resource_slot_diff: ResourceSlot
    ) -> None:
        """
        Update agent resource allocation by adding the slot difference.
        """
        async with self._db.begin_session() as session:
            await self._update_agent_resource_allocation(session, agent_id, resource_slot_diff)

    async def _update_agent_resource_allocation(
        self, session: SASession, agent_id: AgentId, resource_slot_diff: ResourceSlot
    ) -> None:
        """
        Private method to update agent resource allocation.
        """
        # Get current occupied slots
        query = sa.select(agents.c.occupied_slots).where(agents.c.id == agent_id)
        result = await session.execute(query)
        current_occupied_slots = result.scalar()

        # Calculate new occupied slots
        new_occupied_slots = ResourceSlot.from_json(current_occupied_slots) + resource_slot_diff

        # Update agent occupied slots
        update_query = (
            sa.update(agents)
            .values(occupied_slots=new_occupied_slots)
            .where(agents.c.id == agent_id)
        )
        await session.execute(update_query)

    async def recalc_agent_resource_usage(
        self, occupied_slots_per_agent: dict[str, ResourceSlot]
    ) -> None:
        """
        Recalculate agent resource usage based on actual kernel occupancy.
        """
        from ai.backend.manager.models.agent import AgentStatus

        async with self._db.begin_session() as session:
            if len(occupied_slots_per_agent) > 0:
                # Update occupied_slots for agents with running containers
                await session.execute(
                    (
                        sa.update(agents)
                        .where(agents.c.id == sa.bindparam("agent_id"))
                        .values(occupied_slots=sa.bindparam("occupied_slots"))
                    ),
                    [
                        {"agent_id": aid, "occupied_slots": slots}
                        for aid, slots in occupied_slots_per_agent.items()
                    ],
                )
                # Clear occupied_slots for alive agents not in the list
                await session.execute(
                    (
                        sa.update(agents)
                        .values(occupied_slots=ResourceSlot({}))
                        .where(agents.c.status == AgentStatus.ALIVE)
                        .where(sa.not_(agents.c.id.in_(occupied_slots_per_agent.keys())))
                    )
                )
            else:
                # No running containers, clear all agent occupied_slots
                query = (
                    sa.update(agents)
                    .values(occupied_slots=ResourceSlot({}))
                    .where(agents.c.status == AgentStatus.ALIVE)
                )
                await session.execute(query)

    async def handle_agent_heartbeat(
        self,
        agent_id: AgentId,
        agent_info: dict,
        slot_key_and_units: dict,
        auto_terminate_abusing_kernel: bool,
    ) -> tuple[bool, Optional[dict], bool]:
        """
        Handle agent heartbeat with database operations.
        Returns: (instance_rejoin, agent_row, should_update_cache)
        """
        from datetime import datetime, timezone

        from ai.backend.manager.models.agent import AgentStatus

        now = datetime.now(timezone.utc)
        instance_rejoin = False
        should_update_cache = False

        async with self._db.begin() as conn:
            # Fetch agent with lock
            fetch_query = (
                sa.select([
                    agents.c.status,
                    agents.c.addr,
                    agents.c.public_host,
                    agents.c.public_key,
                    agents.c.scaling_group,
                    agents.c.available_slots,
                    agents.c.version,
                    agents.c.compute_plugins,
                    agents.c.architecture,
                    agents.c.auto_terminate_abusing_kernel,
                ])
                .select_from(agents)
                .where(agents.c.id == agent_id)
                .with_for_update()
            )
            result = await conn.execute(fetch_query)
            row = result.first()

            if row is None or row["status"] is None:
                # New agent - insert
                insert_query = sa.insert(agents).values({
                    "id": agent_id,
                    "status": AgentStatus.ALIVE,
                    "region": agent_info["region"],
                    "scaling_group": agent_info["scaling_group"],
                    "available_slots": agent_info["available_slots"],
                    "occupied_slots": {},
                    "addr": agent_info["addr"],
                    "public_host": agent_info["public_host"],
                    "public_key": agent_info["public_key"],
                    "first_contact": now,
                    "lost_at": sa.null(),
                    "version": agent_info["version"],
                    "compute_plugins": agent_info["compute_plugins"],
                    "architecture": agent_info.get("architecture", "x86_64"),
                    "auto_terminate_abusing_kernel": auto_terminate_abusing_kernel,
                })
                result = await conn.execute(insert_query)
                should_update_cache = True
                return instance_rejoin, None, should_update_cache

            elif row["status"] == AgentStatus.ALIVE:
                # Update existing alive agent
                updates = {}
                invalidate_agent_cache = False

                if row["available_slots"] != agent_info["available_slots"]:
                    updates["available_slots"] = agent_info["available_slots"]
                if row["scaling_group"] != agent_info["scaling_group"]:
                    updates["scaling_group"] = agent_info["scaling_group"]
                if row["addr"] != agent_info["addr"]:
                    updates["addr"] = agent_info["addr"]
                    invalidate_agent_cache = True
                if row["public_host"] != agent_info["public_host"]:
                    updates["public_host"] = agent_info["public_host"]
                if row["public_key"] != agent_info["public_key"]:
                    updates["public_key"] = agent_info["public_key"]
                    invalidate_agent_cache = True
                if row["version"] != agent_info["version"]:
                    updates["version"] = agent_info["version"]
                if row["compute_plugins"] != agent_info["compute_plugins"]:
                    updates["compute_plugins"] = agent_info["compute_plugins"]
                if row["architecture"] != agent_info["architecture"]:
                    updates["architecture"] = agent_info["architecture"]
                if row["auto_terminate_abusing_kernel"] != auto_terminate_abusing_kernel:
                    updates["auto_terminate_abusing_kernel"] = auto_terminate_abusing_kernel

                if updates:
                    update_query = sa.update(agents).values(updates).where(agents.c.id == agent_id)
                    await conn.execute(update_query)

                should_update_cache = invalidate_agent_cache
                return instance_rejoin, dict(row._mapping), should_update_cache

            elif row["status"] in (AgentStatus.LOST, AgentStatus.TERMINATED):
                # Rejoin previously lost/terminated agent
                instance_rejoin = True
                update_query = (
                    sa.update(agents)
                    .values({
                        "status": AgentStatus.ALIVE,
                        "available_slots": agent_info["available_slots"],
                        "occupied_slots": {},
                        "addr": agent_info["addr"],
                        "public_host": agent_info["public_host"],
                        "public_key": agent_info["public_key"],
                        "lost_at": sa.null(),
                        "version": agent_info["version"],
                        "compute_plugins": agent_info["compute_plugins"],
                        "architecture": agent_info.get("architecture", "x86_64"),
                        "auto_terminate_abusing_kernel": auto_terminate_abusing_kernel,
                    })
                    .where(agents.c.id == agent_id)
                )
                await conn.execute(update_query)
                should_update_cache = True
                return instance_rejoin, dict(row._mapping), should_update_cache

            return instance_rejoin, dict(row._mapping) if row else None, should_update_cache

    async def mark_agent_lost(self, agent_id: AgentId) -> None:
        """
        Mark agent as lost.
        """
        from datetime import datetime, timezone

        from ai.backend.manager.models.agent import AgentStatus

        now = datetime.now(timezone.utc)
        async with self._db.begin() as conn:
            update_query = (
                sa.update(agents)
                .values({
                    "status": AgentStatus.LOST,
                    "lost_at": now,
                })
                .where(agents.c.id == agent_id)
            )
            await conn.execute(update_query)
