from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.kernel_group import KernelGroupID
from ai.backend.common.data.entity.session import SessionEntityType, SessionID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.field.bulk_lookup import LookupBulkFieldOwnerOpsAction
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.models.kernel_group.lookups import KernelGroupOwnerLookup


@dataclass(frozen=True)
class KernelGroupIDLookupKey(LookupKey):
    """A kernel group row's id, resolved into the session it belongs to."""

    kernel_group_id: KernelGroupID

    @override
    def kind(self) -> str:
        return "kernel_group_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"kernel_group_id": str(self.kernel_group_id)}


@dataclass(frozen=True)
class LookupBulkKernelGroupOwnerAction(LookupBulkFieldOwnerOpsAction[KernelGroupID, SessionID]):
    """The sessions several kernel groups belong to."""

    kernel_group_ids: Sequence[KernelGroupID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SessionEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_bulk_kernel_group_owner"

    @override
    def to_lookup_key(self, field_id: KernelGroupID) -> LookupKey:
        return KernelGroupIDLookupKey(field_id)

    @override
    def field_ids(self) -> Sequence[KernelGroupID]:
        return tuple(self.kernel_group_ids)

    @override
    def to_owner_lookup(self) -> KernelGroupOwnerLookup:
        return KernelGroupOwnerLookup()
