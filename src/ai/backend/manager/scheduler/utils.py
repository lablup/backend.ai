from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from ai.backend.common.types import (
    ResourceSlot,
)

from ..api.exceptions import GenericBadRequest

if TYPE_CHECKING:
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
