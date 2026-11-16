from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.kernel_group_environ import KernelGroupEnvironID
from ai.backend.common.data.entity.session import SessionEntityType, SessionID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.field.bulk_lookup import LookupBulkFieldOwnerOpsAction
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.models.kernel_group_environ.lookups import KernelGroupEnvironOwnerLookup


@dataclass(frozen=True)
class KernelGroupEnvironIDLookupKey(LookupKey):
    """A kernel group environ row's id, resolved into the session it belongs to."""

    kernel_group_environ_id: KernelGroupEnvironID

    @override
    def kind(self) -> str:
        return "kernel_group_environ_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"kernel_group_environ_id": str(self.kernel_group_environ_id)}


@dataclass(frozen=True)
class LookupBulkKernelGroupEnvironOwnerAction(
    LookupBulkFieldOwnerOpsAction[KernelGroupEnvironID, SessionID]
):
    """The sessions several kernel group environ rows belong to."""

    kernel_group_environ_ids: Sequence[KernelGroupEnvironID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SessionEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_bulk_kernel_group_environ_owner"

    @override
    def to_lookup_key(self, field_id: KernelGroupEnvironID) -> LookupKey:
        return KernelGroupEnvironIDLookupKey(field_id)

    @override
    def field_ids(self) -> Sequence[KernelGroupEnvironID]:
        return tuple(self.kernel_group_environ_ids)

    @override
    def to_owner_lookup(self) -> KernelGroupEnvironOwnerLookup:
        return KernelGroupEnvironOwnerLookup()
