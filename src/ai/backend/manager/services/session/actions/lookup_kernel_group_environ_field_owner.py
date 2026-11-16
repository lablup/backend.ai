from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.kernel_group_environ import KernelGroupEnvironID
from ai.backend.common.data.entity.session import SessionEntityType, SessionID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.field.lookup import LookupFieldOwnerOpsAction
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.models.kernel_group_environ.lookups import KernelGroupEnvironOwnerLookup
from ai.backend.manager.services.session.actions.lookup_bulk_kernel_group_environ_owner import (
    KernelGroupEnvironIDLookupKey,
)


@dataclass(frozen=True)
class LookupKernelGroupEnvironFieldOwnerAction(
    LookupFieldOwnerOpsAction[KernelGroupEnvironID, SessionID]
):
    """The session a kernel group environ row belongs to."""

    kernel_group_environ_id: KernelGroupEnvironID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SessionEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_kernel_group_environ_field_owner"

    @override
    def lookup_key(self) -> LookupKey:
        return KernelGroupEnvironIDLookupKey(self.kernel_group_environ_id)

    @override
    def field_id(self) -> KernelGroupEnvironID:
        return self.kernel_group_environ_id

    @override
    def to_owner_lookup(self) -> KernelGroupEnvironOwnerLookup:
        return KernelGroupEnvironOwnerLookup()
