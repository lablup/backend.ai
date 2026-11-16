from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.kernel_group_resource_slot import KernelGroupResourceSlotID
from ai.backend.common.data.entity.session import SessionEntityType, SessionID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.field.bulk_lookup import LookupBulkFieldOwnerOpsAction
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.models.kernel_group_resource_slot.lookups import (
    KernelGroupResourceSlotOwnerLookup,
)


@dataclass(frozen=True)
class KernelGroupResourceSlotIDLookupKey(LookupKey):
    """A kernel group resource slot row's id, resolved into the session it belongs to."""

    kernel_group_resource_slot_id: KernelGroupResourceSlotID

    @override
    def kind(self) -> str:
        return "kernel_group_resource_slot_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"kernel_group_resource_slot_id": str(self.kernel_group_resource_slot_id)}


@dataclass(frozen=True)
class LookupBulkKernelGroupResourceSlotOwnerAction(
    LookupBulkFieldOwnerOpsAction[KernelGroupResourceSlotID, SessionID]
):
    """The sessions several kernel group resource slot rows belong to."""

    kernel_group_resource_slot_ids: Sequence[KernelGroupResourceSlotID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SessionEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_bulk_kernel_group_resource_slot_owner"

    @override
    def to_lookup_key(self, field_id: KernelGroupResourceSlotID) -> LookupKey:
        return KernelGroupResourceSlotIDLookupKey(field_id)

    @override
    def field_ids(self) -> Sequence[KernelGroupResourceSlotID]:
        return tuple(self.kernel_group_resource_slot_ids)

    @override
    def to_owner_lookup(self) -> KernelGroupResourceSlotOwnerLookup:
        return KernelGroupResourceSlotOwnerLookup()
