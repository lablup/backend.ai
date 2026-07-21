"""
Utility functions for agent selectors.
"""

from decimal import Decimal

from ai.backend.common.types import SlotName
from ai.backend.manager.data.sokovan import AgentInfo
from ai.backend.manager.data.sokovan.workload import ResourceRequest


def count_unutilized_capabilities(agent_info: AgentInfo, request: ResourceRequest) -> int:
    """
    Count the number of capabilities (resource types) that the agent has available
    but are not being utilized by the request.

    This helps in selecting agents that don't have too many unutilized capabilities,
    which can improve resource utilization efficiency.

    Args:
        agent_info: Information about the agent
        request: Resource request of the session/kernel

    Returns:
        Number of unutilized capabilities (resource types with zero request but available on agent)
    """
    # Find slots that are requested as zero (not needed)
    zero_requested_slots = {
        slot_name for slot_name, amount in request.slots.items() if amount == Decimal(0)
    }

    # Count how many of these zero-requested slots the agent has available
    unutilized_count = 0
    for slot_name, resource in agent_info.resources.slots.items():
        if (
            slot_name in zero_requested_slots
            and resource.capacity - resource.reserved - resource.used > Decimal(0)
        ):
            unutilized_count += 1

    return unutilized_count


def order_slots_by_priority(
    request: ResourceRequest,
    priority_order: list[str],
) -> list[SlotName]:
    """
    Order the requested slot names according to the given priority list.

    Slots in the priority list come first in order, followed by
    any remaining slots in alphabetical order.

    Args:
        request: Resource request whose slot names are ordered
        priority_order: List of slot names in priority order

    Returns:
        Ordered list of slot names
    """
    requested_slot_names = set(request.slots.keys())

    # First, include slots that are in the priority list
    prioritized_slots = [
        SlotName(slot_name)
        for slot_name in priority_order
        if SlotName(slot_name) in requested_slot_names
    ]

    # Then, add remaining slots in sorted order
    remaining_slots = sorted(requested_slot_names - set(prioritized_slots))

    return prioritized_slots + remaining_slots
