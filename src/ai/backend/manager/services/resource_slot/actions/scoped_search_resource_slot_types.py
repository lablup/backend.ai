"""Resource slot type search over the scopes a slot type is reachable from."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_slot import ResourceSlotTypeEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import ScopedSearchOpsAction
from ai.backend.manager.data.resource_slot.types import ResourceSlotTypeData
from ai.backend.manager.models.resource_slot.row import ResourceSlotTypeRow

__all__ = ("ScopedSearchResourceSlotTypesAction",)


@dataclass(frozen=True)
class ScopedSearchResourceSlotTypesAction(
    ScopedSearchOpsAction[ResourceSlotTypeRow, ResourceSlotTypeData]
):
    """Page through the slot types the named scopes reach, combined with OR.

    Every scope is authorized and every using entity must be readable before the read
    runs, so a caller reaching for one they cannot see is refused rather than served the
    rest.
    """

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ResourceSlotTypeEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_resource_slot_types"
