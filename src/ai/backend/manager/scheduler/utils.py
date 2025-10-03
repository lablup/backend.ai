from __future__ import annotations

import sys
from collections.abc import Sequence
from typing import TYPE_CHECKING

from ai.backend.common.types import (
    ResourceSlot,
    SlotName,
)

from ..errors.common import GenericBadRequest

if TYPE_CHECKING:
    from ..models.session import SessionRow


def sort_requested_slots_by_priority(
    requested_slots: ResourceSlot, priority_list: Sequence[str | SlotName]
) -> list[SlotName]:
    """
    Sort ``requested_slots``'s keys by the given ``agent_selection_resource_priority`` list.
    """

    def get_slot_index(slotname: str | SlotName, priority_list: list[str | SlotName]) -> int:
        try:
            return priority_list.index(slotname)
        except ValueError:
            return sys.maxsize

    # Fill missing concrete slot names, by inserting slot names after corresponding device names.
    priority_list_with_slot_names = [*priority_list]
    for requested_slot_key in sorted(requested_slots.data.keys(), reverse=True):
        device_name = requested_slot_key.device_name
        if requested_slot_key not in priority_list and device_name in priority_list:
            priority_list_with_slot_names.insert(
                priority_list_with_slot_names.index(device_name) + 1, requested_slot_key
            )

    return sorted(
        requested_slots.data.keys(),
        key=lambda item: get_slot_index(item, priority_list_with_slot_names),
    )


def get_requested_architecture(sess_ctx: SessionRow) -> str:
    requested_architectures = set(k.architecture for k in sess_ctx.kernels)
    if len(requested_architectures) > 1:
        raise GenericBadRequest(
            "Cannot assign multiple kernels with different architectures' single node session",
        )
    return requested_architectures.pop()
