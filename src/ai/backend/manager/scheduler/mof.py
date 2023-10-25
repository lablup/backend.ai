from __future__ import annotations

from typing import Optional, Sequence

import trafaret as t

from ai.backend.common.types import (
    AccessKey,
    AgentId,
    AgentSelectionStrategy,
    ResourceSlot,
    SessionId,
)
from ai.backend.manager.scheduler.utils import select_agent

from ..models import AgentRow, SessionRow
from .types import AbstractScheduler, KernelInfo, SchedulingContext


class MOFScheduler(AbstractScheduler):
    """Minimum Occupied slot First Scheduler"""

    config_iv = t.Dict({}).allow_extra("*")

    def pick_session(
        self,
        total_capacity: ResourceSlot,
        pending_sessions: Sequence[SessionRow],
        existing_sessions: Sequence[SessionRow],
    ) -> Optional[SessionId]:
        # Just pick the first pending session.
        return SessionId(pending_sessions[0].id)

    def _assign_agent(
        self,
        agents: Sequence[AgentRow],
        access_key: AccessKey,
        requested_slots: ResourceSlot,
        agent_selection_strategy: AgentSelectionStrategy,
        agent_selection_resource_priority: list[str],
    ) -> Optional[AgentId]:
        # return min occupied slot agent or None
        return next(
            (
                one_agent.id
                for one_agent in (
                    sorted(
                        (
                            agent
                            for agent in agents
                            if ((agent.available_slots - agent.occupied_slots) >= requested_slots)
                        ),
                        key=lambda agent: agent.occupied_slots,
                    )
                )
            ),
            None,
        )

    async def assign_agent_for_session(
        self,
        possible_agents: Sequence[AgentRow],
        pending_session: SessionRow,
        agent_selection_strategy: AgentSelectionStrategy,
        agent_selection_resource_priority: list[str],
        sgroup_name: Optional[str] = None,
        sched_ctx: Optional[SchedulingContext] = None,
        requested_architecture: Optional[str] = None,
    ) -> Optional[AgentId]:
        return await select_agent(
            possible_agents,
            pending_session,
            agent_selection_strategy,
            agent_selection_resource_priority,
            sgroup_name,
            sched_ctx,
            requested_architecture,
        )

    async def assign_agent_for_kernel(
        self,
        possible_agents: Sequence[AgentRow],
        pending_kernel: KernelInfo,
        agent_selection_strategy: AgentSelectionStrategy,
        agent_selection_resource_priority: list[str],
        sgroup_name: Optional[str] = None,
        sched_ctx: Optional[SchedulingContext] = None,
        requested_architecture: Optional[str] = None,
    ) -> Optional[AgentId]:
        return await select_agent(
            possible_agents,
            pending_kernel,
            agent_selection_strategy,
            agent_selection_resource_priority,
            sgroup_name,
            sched_ctx,
            requested_architecture,
        )
