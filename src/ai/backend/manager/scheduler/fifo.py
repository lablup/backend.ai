from __future__ import annotations

import sys
from decimal import Decimal
from typing import List, Optional, Sequence, Tuple

import trafaret as t

from ai.backend.common.types import (
    AgentId,
    AgentSelectionStrategy,
    ResourceSlot,
    SessionId,
)

from ..models import AgentRow, SessionRow
from .types import AbstractScheduler, KernelInfo


def get_slot_index(slotname: str, agent_selection_resource_priority: list[str]) -> int:
    try:
        return agent_selection_resource_priority.index(slotname)
    except ValueError:
        return sys.maxsize


def key_by_remaining_slots(
    agent: AgentRow,
    requested_slots: ResourceSlot,
    agent_selection_strategy: AgentSelectionStrategy,
    agent_selection_resource_priority: list[str],
) -> Tuple[int, ...]:
    unused_slot_keys = set()
    for k, v in requested_slots.items():
        if v == Decimal(0):
            unused_slot_keys.add(k)
    num_extras = 0
    for k, v in agent.available_slots.items():
        if k in unused_slot_keys and v > Decimal(0):
            num_extras += 1

    for requested_slot_key in sorted(requested_slots.data.keys(), reverse=True):
        device_name = requested_slot_key.split(".")[0]
        if (
            requested_slot_key not in agent_selection_resource_priority
            and device_name in agent_selection_resource_priority
        ):
            agent_selection_resource_priority.insert(
                agent_selection_resource_priority.index(device_name) + 1, requested_slot_key
            )

    resource_priorities = sorted(
        requested_slots.data.keys(),
        key=lambda item: get_slot_index(item, agent_selection_resource_priority),
    )

    remaining_slots = agent.available_slots - agent.occupied_slots

    # If the requested slot does not exist in the corresponding agent,
    # the agent should not be selected, in this case it puts -math.inf for avoiding to being selected.
    match agent_selection_strategy:
        case AgentSelectionStrategy.LEGACY:
            comparators = [
                agent.available_slots.get(key, -sys.maxsize) for key in resource_priorities
            ]
        case AgentSelectionStrategy.CONCENTRATED:
            comparators = [-remaining_slots.get(key, sys.maxsize) for key in resource_priorities]
        case AgentSelectionStrategy.DISPERSED | _:
            comparators = [remaining_slots.get(key, -sys.maxsize) for key in resource_priorities]

    # Put back agents with more extra slot types
    # (e.g., accelerators)
    # Also put front agents with exactly required slot types
    return (-num_extras, *comparators)


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

    def _assign_agent(
        self,
        agents: Sequence[AgentRow],
        requested_slots: ResourceSlot,
        agent_selection_strategy: AgentSelectionStrategy,
        agent_selection_resource_priority: list[str],
    ) -> Optional[AgentId]:
        possible_agents = []
        for agent in agents:
            remaining_slots = agent.available_slots - agent.occupied_slots
            if remaining_slots >= requested_slots:
                possible_agents.append(agent)
        if possible_agents:
            chosen_agent = max(
                possible_agents,
                key=lambda agent: key_by_remaining_slots(
                    agent,
                    requested_slots,
                    agent_selection_strategy,
                    agent_selection_resource_priority,
                ),
            )
            return chosen_agent.id
        return None

    def assign_agent_for_session(
        self,
        agents: Sequence[AgentRow],
        pending_session: SessionRow,
        agent_selection_strategy: AgentSelectionStrategy,
        agent_selection_resource_priority: list[str],
    ) -> Optional[AgentId]:
        return self._assign_agent(
            agents,
            pending_session.requested_slots,
            agent_selection_strategy,
            agent_selection_resource_priority,
        )

    def assign_agent_for_kernel(
        self,
        agents: Sequence[AgentRow],
        pending_kernel: KernelInfo,
        agent_selection_strategy: AgentSelectionStrategy,
        agent_selection_resource_priority: list[str],
    ) -> Optional[AgentId]:
        return self._assign_agent(
            agents,
            pending_kernel.requested_slots,
            agent_selection_strategy,
            agent_selection_resource_priority,
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

    def _assign_agent(
        self,
        agents: Sequence[AgentRow],
        requested_slots: ResourceSlot,
        agent_selection_strategy: AgentSelectionStrategy,
        agent_selection_resource_priority: list[str],
    ) -> Optional[AgentId]:
        possible_agents = []
        for agent in agents:
            remaining_slots = agent.available_slots - agent.occupied_slots
            if remaining_slots >= requested_slots:
                possible_agents.append(agent)
        if possible_agents:
            chosen_agent = max(
                possible_agents,
                key=lambda agent: key_by_remaining_slots(
                    agent,
                    requested_slots,
                    agent_selection_strategy,
                    agent_selection_resource_priority,
                ),
            )
            return chosen_agent.id
        return None

    def assign_agent_for_session(
        self,
        agents: Sequence[AgentRow],
        pending_session: SessionRow,
        agent_selection_strategy: AgentSelectionStrategy,
        agent_selection_resource_priority: list[str],
    ) -> Optional[AgentId]:
        return self._assign_agent(
            agents,
            pending_session.requested_slots,
            agent_selection_strategy,
            agent_selection_resource_priority,
        )

    def assign_agent_for_kernel(
        self,
        agents: Sequence[AgentRow],
        pending_kernel: KernelInfo,
        agent_selection_strategy: AgentSelectionStrategy,
        agent_selection_resource_priority: list[str],
    ) -> Optional[AgentId]:
        return self._assign_agent(
            agents,
            pending_kernel.requested_slots,
            agent_selection_strategy,
            agent_selection_resource_priority,
        )
