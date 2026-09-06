from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.kernel import KernelID
from ai.backend.common.data.entity.session import SESSION_ENTITY_TYPE, SessionID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.field.bulk_lookup import LookupBulkFieldOwnerOpsAction
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.models.kernel.lookups import KernelOwnerLookup


@dataclass(frozen=True)
class KernelIDLookupKey(LookupKey):
    """A kernel row's id, resolved into the session it runs under."""

    kernel_id: KernelID

    @override
    def kind(self) -> str:
        return "kernel_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"kernel_id": str(self.kernel_id)}


@dataclass
class LookupBulkKernelOwnerAction(LookupBulkFieldOwnerOpsAction[KernelID, SessionID]):
    """The sessions several kernels run under."""

    kernel_ids: Sequence[KernelID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SESSION_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_bulk_kernel_owner"

    @override
    def to_lookup_key(self, field_id: KernelID) -> LookupKey:
        return KernelIDLookupKey(field_id)

    @override
    def field_ids(self) -> Sequence[KernelID]:
        return tuple(self.kernel_ids)

    @override
    def to_owner_lookup(self) -> KernelOwnerLookup:
        return KernelOwnerLookup()
