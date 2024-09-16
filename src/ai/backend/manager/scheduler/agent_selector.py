from __future__ import annotations

import dataclasses
import logging
import sys
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Optional, Self, Sequence, override

import trafaret as t

from ai.backend.common.types import (
    AgentId,
    ArchName,
    JSONSerializableMixin,
    ResourceSlot,
)

from ..models import AgentRow, KernelRow, SessionRow
from .types import (
    AbstractAgentSelector,
    NullAgentSelectionState,
    ResourceGroupState,
    T_ResourceGroupState,
)
from .utils import (
    get_requested_architecture,
    sort_requested_slots_by_priority,
)

log = logging.Logger(__spec__.name)


def get_num_extras(agent: AgentRow, requested_slots: ResourceSlot) -> int:
    """
    Get the number of resource slots that:
    1) are requested but zero (unused),
    2) are available in the given agent.

    This is to prefer (or not) agents with additional unused slots,
    depending on the selection strategy.
    """
    unused_slot_keys = set()
    for k, v in requested_slots.items():
        if v == Decimal(0):
            unused_slot_keys.add(k)
    num_extras = 0
    for k, v in agent.available_slots.items():
        if k in unused_slot_keys and v > Decimal(0):
            num_extras += 1

    return num_extras


class BaseAgentSelector(AbstractAgentSelector[T_ResourceGroupState]):
    @property
    @override
    def config_iv(self) -> t.Dict:
        return t.Dict({}).allow_extra("*")

    @override
    @classmethod
    def get_state_cls(cls) -> type[T_ResourceGroupState]:
        raise NotImplementedError("must use a concrete subclass")

    def filter_agents(
        self,
        compatible_agents: Sequence[AgentRow],
        pending_session_or_kernel: SessionRow | KernelRow,
    ) -> Sequence[AgentRow]:
        """
        Filter the agents by checking if it can host the picked session.
        """
        return [
            agent
            for agent in compatible_agents
            if (
                agent.available_slots - agent.occupied_slots
                >= pending_session_or_kernel.requested_slots
            )
        ]


class LegacyAgentSelector(BaseAgentSelector[NullAgentSelectionState]):
    @override
    @classmethod
    def get_state_cls(cls) -> type[NullAgentSelectionState]:
        return NullAgentSelectionState

    @override
    async def select_agent(
        self,
        agents: Sequence[AgentRow],
        pending_session_or_kernel: SessionRow | KernelRow,
    ) -> Optional[AgentId]:
        agents = self.filter_agents(agents, pending_session_or_kernel)
        if not agents:
            return None
        requested_slots = pending_session_or_kernel.requested_slots
        resource_priorities = sort_requested_slots_by_priority(
            requested_slots, self.agent_selection_resource_priority
        )
        chosen_agent = max(
            agents,
            key=lambda agent: [
                -get_num_extras(agent, requested_slots),
                *[agent.available_slots.get(key, -sys.maxsize) for key in resource_priorities],
            ],
        )
        return chosen_agent.id


@dataclass
class RoundRobinState(JSONSerializableMixin):
    next_index: int = 0

    @override
    def to_json(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    @override
    @classmethod
    def as_trafaret(cls) -> t.Trafaret:
        return t.Dict({
            t.Key("next_index", default=0): t.ToInt,
        })


@dataclass
class RRAgentSelectorState(ResourceGroupState):
    roundrobin_states: dict[ArchName, RoundRobinState] | None = None

    @override
    @classmethod
    def create_empty_state(cls) -> Self:
        return cls({})

    @override
    @classmethod
    def as_trafaret(cls) -> t.Trafaret:
        return t.Dict({
            t.Key("roundrobin_states"): t.Mapping(t.String, RoundRobinState.as_trafaret()),
        })


class RoundRobinAgentSelector(BaseAgentSelector[RRAgentSelectorState]):
    @override
    @classmethod
    def get_state_cls(cls) -> type[RRAgentSelectorState]:
        return RRAgentSelectorState

    @override
    async def select_agent(
        self,
        agents: Sequence[AgentRow],
        pending_session_or_kernel: SessionRow | KernelRow,
    ) -> Optional[AgentId]:
        if isinstance(pending_session_or_kernel, KernelRow):
            sgroup_name = pending_session_or_kernel.scaling_group
            requested_architecture = ArchName(pending_session_or_kernel.architecture)
        else:
            sgroup_name = pending_session_or_kernel.scaling_group_name
            requested_architecture = ArchName(get_requested_architecture(pending_session_or_kernel))

        agselector_state = await self.state_store.load(sgroup_name, "agselector.roundrobin")
        rr_states = agselector_state.roundrobin_states or {}
        rr_state = rr_states.get(requested_architecture, None)

        if rr_state is None:
            agent_start_idx = 0
        else:
            agent_start_idx = rr_state.next_index % len(agents)

        chosen_agent = None
        agents = sorted(agents, key=lambda agent: agent.id)

        for i in range(len(agents)):
            idx = (agent_start_idx + i) % len(agents)
            if (
                agents[idx].available_slots - agents[idx].occupied_slots
                >= pending_session_or_kernel.requested_slots
            ):
                chosen_agent = agents[idx]
                agselector_state.roundrobin_states = {
                    **rr_states,
                    requested_architecture: RoundRobinState(next_index=(idx + 1) % len(agents)),
                }
                await self.state_store.store(sgroup_name, "agselector.roundrobin", agselector_state)
                break

        if not chosen_agent:
            return None

        return chosen_agent.id


class ConcentratedAgentSelector(BaseAgentSelector[NullAgentSelectionState]):
    @override
    @classmethod
    def get_state_cls(cls) -> type[NullAgentSelectionState]:
        return NullAgentSelectionState

    @override
    async def select_agent(
        self,
        agents: Sequence[AgentRow],
        pending_session_or_kernel: SessionRow | KernelRow,
    ) -> Optional[AgentId]:
        agents = self.filter_agents(agents, pending_session_or_kernel)
        if not agents:
            return None
        requested_slots = pending_session_or_kernel.requested_slots
        resource_priorities = sort_requested_slots_by_priority(
            requested_slots, self.agent_selection_resource_priority
        )
        chosen_agent = min(
            agents,
            key=lambda agent: [
                get_num_extras(agent, requested_slots),
                *[
                    (agent.available_slots - agent.occupied_slots).get(key, sys.maxsize)
                    for key in resource_priorities
                ],
            ],
        )
        return chosen_agent.id


class DispersedAgentSelector(BaseAgentSelector[NullAgentSelectionState]):
    @override
    @classmethod
    def get_state_cls(cls) -> type[NullAgentSelectionState]:
        return NullAgentSelectionState

    @override
    async def select_agent(
        self,
        agents: Sequence[AgentRow],
        pending_session_or_kernel: SessionRow | KernelRow,
    ) -> Optional[AgentId]:
        agents = self.filter_agents(agents, pending_session_or_kernel)
        if not agents:
            return None
        requested_slots = pending_session_or_kernel.requested_slots
        resource_priorities = sort_requested_slots_by_priority(
            requested_slots, self.agent_selection_resource_priority
        )
        chosen_agent = max(
            agents,
            key=lambda agent: [
                -get_num_extras(agent, requested_slots),
                *[
                    (agent.available_slots - agent.occupied_slots).get(key, -sys.maxsize)
                    for key in resource_priorities
                ],
            ],
        )
        return chosen_agent.id
