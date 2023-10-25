import sys
from decimal import Decimal
from typing import Optional, Sequence

from ai.backend.common.types import AgentId, AgentSelectionStrategy, ResourceSlot, RoundRobinState
from ai.backend.manager.api.exceptions import GenericBadRequest
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.scheduler.types import KernelInfo, SchedulingContext


def get_slot_index(slotname: str, agent_selection_resource_priority: list[str]) -> int:
    try:
        return agent_selection_resource_priority.index(slotname)
    except ValueError:
        return sys.maxsize


def sort_requested_slots_by_priority(
    requested_slots: ResourceSlot, agent_selection_resource_priority: list[str]
) -> list[str]:
    """
    Handle 'agent-selection-resource-priority' config for sorting resource priorities.
    """

    for requested_slot_key in sorted(requested_slots.data.keys(), reverse=True):
        device_name = requested_slot_key.split(".")[0]
        if (
            requested_slot_key not in agent_selection_resource_priority
            and device_name in agent_selection_resource_priority
        ):
            agent_selection_resource_priority.insert(
                agent_selection_resource_priority.index(device_name) + 1, requested_slot_key
            )

    return sorted(
        requested_slots.data.keys(),
        key=lambda item: get_slot_index(item, agent_selection_resource_priority),
    )


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


def get_requested_architecture(sess_ctx: SessionRow) -> str:
    requested_architectures = set(k.architecture for k in sess_ctx.kernels)
    if len(requested_architectures) > 1:
        raise GenericBadRequest(
            "Cannot assign multiple kernels with different architectures' single node session",
        )
    return requested_architectures.pop()


async def select_agent(
    possible_agents: Sequence[AgentRow],
    pending_session_or_kernel: SessionRow | KernelInfo,
    agent_selection_strategy: AgentSelectionStrategy,
    agent_selection_resource_priority: list[str],
    sgroup_name: Optional[str] = None,
    sched_ctx: Optional[SchedulingContext] = None,
    requested_architecture: Optional[str] = None,
) -> Optional[AgentId]:
    requested_slots = pending_session_or_kernel.requested_slots

    agent_candidates = [
        agent
        for agent in possible_agents
        if agent.available_slots - agent.occupied_slots >= requested_slots
    ]

    if not agent_candidates:
        return None

    resource_priorities = sort_requested_slots_by_priority(
        requested_slots, agent_selection_resource_priority
    )

    match agent_selection_strategy:
        # Note that ROUNDROBIN is not working with the multi-node multi-container session.
        # It assumes the pending session type is single-node session.
        case AgentSelectionStrategy.ROUNDROBIN:
            assert sgroup_name is not None
            assert sched_ctx is not None
            assert requested_architecture is not None

            rr_state: RoundRobinState | None = (
                await sched_ctx.registry.shared_config.get_roundrobin_state(
                    sgroup_name, requested_architecture
                )
            )

            if rr_state is None:
                agent_idx = 0
            else:
                agent_idx = rr_state.next_index % len(possible_agents)

            # This logic assumes that the list of possible agents is not changed.
            # If the list of possible agents is changed, the next agent will be selected at random by agent_idx.
            # In this case, we will just use the agent_idx for the simplicity.
            chosen_agent = possible_agents[agent_idx]

            rr_state = RoundRobinState((agent_idx + 1) % len(possible_agents))

            await sched_ctx.registry.shared_config.put_roundrobin_state(
                sgroup_name, requested_architecture, rr_state
            )
        case AgentSelectionStrategy.LEGACY:
            chosen_agent = max(
                possible_agents,
                key=lambda agent: [
                    -get_num_extras(agent, requested_slots),
                    *[agent.available_slots.get(key, -sys.maxsize) for key in resource_priorities],
                ],
            )
        case AgentSelectionStrategy.CONCENTRATED:
            chosen_agent = min(
                possible_agents,
                key=lambda agent: [
                    get_num_extras(agent, requested_slots),
                    *[
                        (agent.available_slots - agent.occupied_slots).get(key, sys.maxsize)
                        for key in resource_priorities
                    ],
                ],
            )
        case AgentSelectionStrategy.DISPERSED | _:
            chosen_agent = max(
                possible_agents,
                key=lambda agent: [
                    -get_num_extras(agent, requested_slots),
                    *[
                        (agent.available_slots - agent.occupied_slots).get(key, -sys.maxsize)
                        for key in resource_priorities
                    ],
                ],
            )

    return chosen_agent.id
