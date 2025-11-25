"""
Utility functions for agent selectors.
"""

from decimal import Decimal
from typing import Set

from ai.backend.common.types import ResourceSlot

from .selector import AgentInfo


def count_unutilized_capabilities(agent_info: AgentInfo, requested_slots: ResourceSlot) -> int:
    """
    Count the number of capabilities (resource types) that the agent has available
    but are not being utilized by the request.

    This helps in selecting agents that don't have too many unutilized capabilities,
    which can improve resource utilization efficiency.

    Args:
        agent_info: Information about the agent
        requested_slots: Resource slots requested by the session/kernel

    Returns:
        Number of unutilized capabilities (resource types with zero request but available on agent)
    """
    # Find slots that are requested as zero (not needed)
    zero_requested_slots: Set[str] = set()
    for slot_name, amount in requested_slots.items():
        if amount == Decimal(0):
            zero_requested_slots.add(slot_name)

    # Count how many of these zero-requested slots the agent has available
    unutilized_count = 0
    available_slots = agent_info.available_slots - agent_info.occupied_slots
    for slot_name, amount in available_slots.items():
        if slot_name in zero_requested_slots and amount > Decimal(0):
            unutilized_count += 1

    return unutilized_count


def order_slots_by_priority(
    requested_slots: ResourceSlot,
    priority_order: list[str],
) -> list[str]:
    """
    Order resource slot names according to the given priority list.

    Slots in the priority list come first in order, followed by
    any remaining slots in alphabetical order.

    Args:
        requested_slots: Resource slots to order
        priority_order: List of slot names in priority order

    Returns:
        Ordered list of slot names
    """
    requested_slot_names = set(requested_slots.keys())

    # First, include slots that are in the priority list
    prioritized_slots = [
        slot_name for slot_name in priority_order if slot_name in requested_slot_names
    ]

    # Then, add remaining slots in sorted order
    remaining_slots = sorted(requested_slot_names - set(prioritized_slots))

    return prioritized_slots + remaining_slots
