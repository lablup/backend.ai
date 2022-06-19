from __future__ import annotations

from typing import (
    Optional,
    Sequence,
)

import trafaret as t

from ai.backend.common.types import (
    AccessKey,
    AgentId,
    SessionId,
    ResourceSlot,
)

from .types import (
    AbstractScheduler,
    PendingSession,
    ExistingSession,
    AgentContext,
    KernelInfo,
)
from ..models import SessionRow, AgentRow, KernelRow


class MOFScheduler(AbstractScheduler):
    """Minimum Occupied slot First Scheduler"""

    config_iv = t.Dict({}).allow_extra('*')

    def pick_session(
        self,
        total_capacity: ResourceSlot,
        pending_sessions: Sequence[SessionRow],
        existing_sessions: Sequence[SessionRow],
    ) -> Optional[SessionRow]:
        # Just pick the first pending session.
        return pending_sessions[0]

    def _assign_agent(
        self,
        agents: Sequence[AgentRow],
        access_key: AccessKey,
        requested_slots: ResourceSlot,
    ) -> Optional[AgentRow]:
        # return min occupied slot agent or None
        return next((one_agent for one_agent in (sorted(
            (agent for agent in agents if (
                (agent.available_slots - agent.occupied_slots)
                >= requested_slots
            )),
            key=lambda a: a.occupied_slots)
        )), None)

    def assign_agent_for_session(
        self,
        agents: Sequence[AgentRow],
        pending_session: SessionRow,
    ) -> Optional[AgentRow]:
        return self._assign_agent(
            agents, pending_session.access_key, pending_session.requested_slots,
        )

    def assign_agent_for_kernel(
        self,
        agents: Sequence[AgentRow],
        pending_kernel: KernelRow,
    ) -> Optional[AgentRow]:
        return self._assign_agent(
            agents, pending_kernel.access_key, pending_kernel.requested_slots,
        )
