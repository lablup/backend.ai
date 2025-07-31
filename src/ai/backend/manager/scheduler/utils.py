from __future__ import annotations

import sys
from decimal import Decimal
from typing import TYPE_CHECKING

from ai.backend.common.types import (
    ResourceSlot,
)

from ..errors.common import GenericBadRequest

if TYPE_CHECKING:
    from ..models import AgentRow
    from ..models.session import SessionRow


def get_slot_index(slotname: str, agent_selection_resource_priority: list[str]) -> int:
    try:
        return agent_selection_resource_priority.index(slotname)
    except ValueError:
        return sys.maxsize


def sort_requested_slots_by_priority(
    requested_slots: ResourceSlot, agent_selection_resource_priority: list[str]
) -> list[str]:
    """
    Sort ``requested_slots``'s keys by the given ``agent_selection_resource_priority`` list.
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


def get_requested_architecture(sess_ctx: SessionRow) -> str:
    requested_architectures = set(k.architecture for k in sess_ctx.kernels)
    if len(requested_architectures) > 1:
        raise GenericBadRequest(
            "Cannot assign multiple kernels with different architectures' single node session",
        )
    return requested_architectures.pop()


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
