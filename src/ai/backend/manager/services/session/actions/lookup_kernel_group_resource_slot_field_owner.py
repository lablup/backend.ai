from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.kernel_group_resource_slot import KernelGroupResourceSlotID
from ai.backend.common.data.entity.session import SessionEntityType, SessionID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.field.lookup import LookupFieldOwnerOpsAction
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.models.kernel_group_resource_slot.lookups import (
    KernelGroupResourceSlotOwnerLookup,
)
from ai.backend.manager.services.session.actions.lookup_bulk_kernel_group_resource_slot_owner import (
    KernelGroupResourceSlotIDLookupKey,
)


@dataclass(frozen=True)
class LookupKernelGroupResourceSlotFieldOwnerAction(
    LookupFieldOwnerOpsAction[KernelGroupResourceSlotID, SessionID]
):
    """The session a kernel group resource slot row belongs to."""

    kernel_group_resource_slot_id: KernelGroupResourceSlotID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SessionEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_kernel_group_resource_slot_field_owner"

    @override
    def lookup_key(self) -> LookupKey:
        return KernelGroupResourceSlotIDLookupKey(self.kernel_group_resource_slot_id)

    @override
    def field_id(self) -> KernelGroupResourceSlotID:
        return self.kernel_group_resource_slot_id

    @override
    def to_owner_lookup(self) -> KernelGroupResourceSlotOwnerLookup:
        return KernelGroupResourceSlotOwnerLookup()
