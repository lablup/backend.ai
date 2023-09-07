from __future__ import annotations

import logging
import sys
from collections import defaultdict
from decimal import Decimal
from typing import Any, Dict, Mapping, Optional, Sequence, Set

import trafaret as t

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    AgentSelectionStrategy,
    ResourceSlot,
    SessionId,
)

from ..models import AgentRow, SessionRow
from ..models.scaling_group import ScalingGroupOpts
from .types import AbstractScheduler, KernelInfo

log = BraceStyleAdapter(logging.getLogger("ai.backend.manager.scheduler"))


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
) -> list[Decimal]:
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
    return comparators


class DRFScheduler(AbstractScheduler):
    config_iv = t.Dict({}).allow_extra("*")
    per_user_dominant_share: Dict[AccessKey, Decimal]
    total_capacity: ResourceSlot

    def __init__(self, sgroup_opts: ScalingGroupOpts, config: Mapping[str, Any]) -> None:
        super().__init__(sgroup_opts, config)
        self.per_user_dominant_share = defaultdict(lambda: Decimal(0))

    def pick_session(
        self,
        total_capacity: ResourceSlot,
        pending_sessions: Sequence[SessionRow],
        existing_sessions: Sequence[SessionRow],
    ) -> Optional[SessionId]:
        self.total_capacity = total_capacity

        # Calculate the initial dominant shares of all users.
        for existing_sess in existing_sessions:
            dominant_share = Decimal(0)
            self.total_capacity.sync_keys(existing_sess.occupying_slots)
            for slot, value in existing_sess.occupying_slots.items():
                slot_cap = Decimal(self.total_capacity[slot])
                if slot_cap == 0:
                    continue
                slot_share = Decimal(value) / slot_cap
                if dominant_share < slot_share:
                    dominant_share = slot_share
            if self.per_user_dominant_share[existing_sess.access_key] < dominant_share:
                self.per_user_dominant_share[existing_sess.access_key] = dominant_share
        log.debug("per-user dominant share: {}", dict(self.per_user_dominant_share))

        # Find who has the least dominant share among the pending session.
        users_with_pending_session: Set[AccessKey] = {
            pending_sess.access_key for pending_sess in pending_sessions
        }
        if not users_with_pending_session:
            return None
        least_dominant_share_user, dshare = min(
            ((akey, self.per_user_dominant_share[akey]) for akey in users_with_pending_session),
            key=lambda item: item[1],
        )
        log.debug("least dominant share user: {} ({})", least_dominant_share_user, dshare)

        # Pick the first pending session of the user
        # who has the lowest dominant share.
        for pending_sess in pending_sessions:
            if pending_sess.access_key == least_dominant_share_user:
                return SessionId(pending_sess.id)

        return None

    def _assign_agent(
        self,
        agents: Sequence[AgentRow],
        access_key: AccessKey,
        requested_slots: ResourceSlot,
        agent_selection_strategy: AgentSelectionStrategy,
        agent_selection_resource_priority: list[str],
    ) -> Optional[AgentId]:
        # If some predicate checks for a picked session fail,
        # this method is NOT called at all for the picked session.
        # In such case, we just skip updating self.per_user_dominant_share state
        # and the scheduler dispatcher continues to pick another session within the same scaling group.

        possible_agents = []
        for agent in agents:
            remaining_slots = agent.available_slots - agent.occupied_slots
            if remaining_slots >= requested_slots:
                possible_agents.append(agent)

        if possible_agents:
            # We have one or more agents that can host the picked session.

            # Update the dominant share.
            # This is required to use to the latest dominant share information
            # when iterating over multiple pending sessions in a single scaling group.
            dominant_share_from_request = Decimal(0)
            for slot, value in requested_slots.items():
                self.total_capacity.sync_keys(requested_slots)
                slot_cap = Decimal(self.total_capacity[slot])
                if slot_cap == 0:
                    continue
                slot_share = Decimal(value) / slot_cap
                if dominant_share_from_request < slot_share:
                    dominant_share_from_request = slot_share
            if self.per_user_dominant_share[access_key] < dominant_share_from_request:
                self.per_user_dominant_share[access_key] = dominant_share_from_request

            # Choose the agent.
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
            pending_session.access_key,
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
            pending_kernel.access_key,
            pending_kernel.requested_slots,
            agent_selection_strategy,
            agent_selection_resource_priority,
        )
