from __future__ import annotations

from decimal import Decimal
from typing import List, Optional, Sequence

import trafaret as t

from ai.backend.common.types import (
    AgentId,
    ResourceSlot,
    RoundRobinContext,
    SessionId,
)

from ..models import AgentRow, KernelRow, SessionRow
from .types import AbstractScheduler


def get_num_extras(agent: AgentRow, requested_slots: ResourceSlot) -> int:
    unused_slot_keys = set()
    for k, v in requested_slots.items():
        if v == Decimal(0):
            unused_slot_keys.add(k)
    num_extras = 0
    for k, v in agent.available_slots.items():
        if k in unused_slot_keys and v > Decimal(0):
            num_extras += 1

    return num_extras


class FIFOSlotScheduler(AbstractScheduler):
    config_iv = t.Dict({
        t.Key("num_retries_to_skip", default=0): t.ToInt(gte=0),
    }).allow_extra("*")

    def pick_session(
        self,
        total_capacity: ResourceSlot,
        pending_sessions: Sequence[SessionRow],
        existing_sessions: Sequence[SessionRow],
    ) -> Optional[SessionId]:
        local_pending_sessions = list(pending_sessions)
        skipped_sessions: List[SessionRow] = []
        max_retries = self.config["num_retries_to_skip"]
        while local_pending_sessions:
            # Just pick the first pending session, but skip it
            # if it has more than 3 failures.
            s = local_pending_sessions.pop(0)
            if max_retries == 0:  # it's strict FIFO
                return s.id
            if s.status_data is not None:
                sched_data = s.status_data.get("scheduler", {})
                if sched_data.get("retries", 0) >= max_retries:
                    skipped_sessions.append(s)
                    continue
            return s.id
        # But if all sessions are skipped, then choose the first one.
        if skipped_sessions:
            return skipped_sessions[0].id
        return None

    async def assign_agent_for_session(
        self,
        agents: Sequence[AgentRow],
        pending_session: SessionRow,
        roundrobin_context: Optional[RoundRobinContext] = None,
    ) -> Optional[AgentId]:
        return await self.select_agent(
            agents,
            pending_session,
            True,
            roundrobin_context,
        )

    async def assign_agent_for_kernel(
        self,
        agents: Sequence[AgentRow],
        pending_kernel: KernelRow,
    ) -> Optional[AgentId]:
        return await self.select_agent(
            agents,
            pending_kernel,
            True,
        )


class LIFOSlotScheduler(AbstractScheduler):
    config_iv = t.Dict({}).allow_extra("*")

    def pick_session(
        self,
        total_capacity: ResourceSlot,
        pending_sessions: Sequence[SessionRow],
        existing_sessions: Sequence[SessionRow],
    ) -> Optional[SessionId]:
        # Just pick the last pending session.
        return SessionId(pending_sessions[-1].id)

    async def assign_agent_for_session(
        self,
        agents: Sequence[AgentRow],
        pending_session: SessionRow,
        roundrobin_context: Optional[RoundRobinContext] = None,
    ) -> Optional[AgentId]:
        return await self.select_agent(
            agents,
            pending_session,
            True,
            roundrobin_context,
        )

    async def assign_agent_for_kernel(
        self,
        agents: Sequence[AgentRow],
        pending_kernel: KernelRow,
    ) -> Optional[AgentId]:
        return await self.select_agent(
            agents,
            pending_kernel,
            True,
        )
