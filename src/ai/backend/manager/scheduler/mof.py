from __future__ import annotations

from typing import Optional, Sequence, Tuple

import trafaret as t

from ai.backend.common.types import (
    AccessKey,
    AgentId,
    AgentSelectionStrategy,
    ResourceSlot,
    SessionId,
)

from ..models import AgentRow, SessionRow
from .types import AbstractScheduler, KernelInfo


def key_by_occupied_slots(
    agent: AgentRow,
    agent_selection_strategy: AgentSelectionStrategy,
) -> Tuple[int, ResourceSlot]:
    comparator = None
    match agent_selection_strategy:
        case AgentSelectionStrategy.LEGACY:
            comparator = agent.occupied_slots
        case AgentSelectionStrategy.CONCENTRATED:
            comparator = -agent.occupied_slots
        case AgentSelectionStrategy.DISPERSED | _:
            comparator = agent.occupied_slots

    return comparator


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
                        key=lambda agent: key_by_occupied_slots(agent, agent_selection_strategy),
                    )
                )
            ),
            None,
        )

    def assign_agent_for_session(
        self,
        agents: Sequence[AgentRow],
        pending_session: SessionRow,
        agent_selection_strategy: AgentSelectionStrategy,
    ) -> Optional[AgentId]:
        return self._assign_agent(
            agents,
            pending_session.access_key,
            pending_session.requested_slots,
            agent_selection_strategy,
        )

    def assign_agent_for_kernel(
        self,
        agents: Sequence[AgentRow],
        pending_kernel: KernelInfo,
        agent_selection_strategy: AgentSelectionStrategy,
    ) -> Optional[AgentId]:
        return self._assign_agent(
            agents,
            pending_kernel.access_key,
            pending_kernel.requested_slots,
            agent_selection_strategy,
        )
