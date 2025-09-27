"""
Utility functions for agent selectors.
"""

import sys
from collections.abc import Sequence
from decimal import Decimal
from typing import Set

from ai.backend.common.types import ResourceSlot, SlotName

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
    zero_requested_slots: Set[SlotName] = set()
    for slot_name, amount in requested_slots.items():
        if amount == Decimal(0):
            zero_requested_slots.add(slot_name)

    # Count how many of these zero-requested slots the agent has available
    unutilized_count = 0
    available_slots = agent_info.available_slots - agent_info.occupied_slots
    for slot_name, amount in available_slots.items():
        if slot_name in zero_requested_slots and Decimal(amount) > Decimal(0):
            unutilized_count += 1

    return unutilized_count


def order_slots_by_priority(
    requested_slots: ResourceSlot,
    priority_order: Sequence[str | SlotName],
) -> list[SlotName]:
    """
    Order resource slot names according to the given priority list.

    The priority order list is declared using device names like "cpu", "cuda", etc.,
    so this function first fills it with concrete resource slot names like "cuda.device"
    by inserting them after corresponding device names like "cuda".

    Args:
        requested_slots: Resource slot instance to get the allocation ordering
        priority_order: A reference list of device names and slot names representing the allocation order

    Returns:
        An ordered list of slot names
    """

    def get_slot_index(slot_name: str | SlotName, order_reference: list[str | SlotName]) -> int:
        try:
            return order_reference.index(slot_name)
        except ValueError:
            return sys.maxsize

    # Fill missing concrete slot names, by inserting slot names after corresponding device names.
    priority_order_including_slot_names = [*priority_order]
    for requested_slot_key in sorted(requested_slots.data.keys(), reverse=True):
        device_name = requested_slot_key.device_name
        if requested_slot_key not in priority_order and device_name in priority_order:
            priority_order_including_slot_names.insert(
                priority_order_including_slot_names.index(device_name) + 1, requested_slot_key
            )

    return sorted(
        requested_slots.data.keys(),
        key=lambda item: get_slot_index(item, priority_order_including_slot_names),
    )
