from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.resource_slot.types import ResourceAllocationData
from ai.backend.manager.models.resource_slot.row import ResourceAllocationRow


@dataclass(frozen=True)
class GlobalSearchResourceAllocationsAction(
    GlobalSearcherOpsAction[ResourceAllocationRow, ResourceAllocationData]
):
    """Page through the slot amounts recorded across the installation."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SessionEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_resource_allocations"
