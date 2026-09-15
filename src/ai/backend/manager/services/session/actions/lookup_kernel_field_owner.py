from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.kernel import KernelID
from ai.backend.common.data.entity.session import SessionEntityType, SessionID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.field.lookup import LookupFieldOwnerOpsAction
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.models.kernel.lookups import KernelOwnerLookup
from ai.backend.manager.services.session.actions.lookup_bulk_kernel_owner import (
    KernelIDLookupKey,
)


@dataclass
class LookupKernelFieldOwnerAction(LookupFieldOwnerOpsAction[KernelID, SessionID]):
    """The session a kernel runs under."""

    kernel_id: KernelID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SessionEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_kernel_field_owner"

    @override
    def lookup_key(self) -> LookupKey:
        return KernelIDLookupKey(self.kernel_id)

    @override
    def field_id(self) -> KernelID:
        return self.kernel_id

    @override
    def to_owner_lookup(self) -> KernelOwnerLookup:
        return KernelOwnerLookup()
