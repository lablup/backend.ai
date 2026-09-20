from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.resource_allocation import ResourceAllocationID
from ai.backend.common.data.entity.session import SessionEntityType, SessionID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.field.bulk_lookup import LookupBulkFieldOwnerOpsAction
from ai.backend.manager.actions.v2.field.lookup import LookupFieldOwnerOpsAction
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.models.resource_slot.lookups import ResourceAllocationOwnerLookup


@dataclass(frozen=True)
class ResourceAllocationIDLookupKey(LookupKey):
    """An allocation row's id, resolved into the session that owns it."""

    allocation_id: ResourceAllocationID

    @override
    def kind(self) -> str:
        return "resource_allocation_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"id": str(self.allocation_id)}


@dataclass
class LookupResourceAllocationOwnerAction(
    LookupFieldOwnerOpsAction[ResourceAllocationID, SessionID]
):
    """The session an allocation row belongs to."""

    allocation_id: ResourceAllocationID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SessionEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_resource_allocation_owner"

    @override
    def lookup_key(self) -> LookupKey:
        return ResourceAllocationIDLookupKey(self.allocation_id)

    @override
    def field_id(self) -> ResourceAllocationID:
        return self.allocation_id

    @override
    def to_owner_lookup(self) -> ResourceAllocationOwnerLookup:
        return ResourceAllocationOwnerLookup()


@dataclass
class LookupBulkResourceAllocationOwnerAction(
    LookupBulkFieldOwnerOpsAction[ResourceAllocationID, SessionID]
):
    """The sessions several allocation rows belong to."""

    allocation_ids: Sequence[ResourceAllocationID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SessionEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_bulk_resource_allocation_owner"

    @override
    def to_lookup_key(self, field_id: ResourceAllocationID) -> LookupKey:
        return ResourceAllocationIDLookupKey(field_id)

    @override
    def field_ids(self) -> Sequence[ResourceAllocationID]:
        return tuple(self.allocation_ids)

    @override
    def to_owner_lookup(self) -> ResourceAllocationOwnerLookup:
        return ResourceAllocationOwnerLookup()
