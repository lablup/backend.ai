from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.kernel_group import KernelGroupID
from ai.backend.common.data.entity.session import SessionEntityType, SessionID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.field.lookup import LookupFieldOwnerOpsAction
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.models.kernel_group.lookups import KernelGroupOwnerLookup
from ai.backend.manager.services.session.actions.lookup_bulk_kernel_group_owner import (
    KernelGroupIDLookupKey,
)


@dataclass(frozen=True)
class LookupKernelGroupFieldOwnerAction(LookupFieldOwnerOpsAction[KernelGroupID, SessionID]):
    """The session a kernel group belongs to."""

    kernel_group_id: KernelGroupID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SessionEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_kernel_group_field_owner"

    @override
    def lookup_key(self) -> LookupKey:
        return KernelGroupIDLookupKey(self.kernel_group_id)

    @override
    def field_id(self) -> KernelGroupID:
        return self.kernel_group_id

    @override
    def to_owner_lookup(self) -> KernelGroupOwnerLookup:
        return KernelGroupOwnerLookup()
