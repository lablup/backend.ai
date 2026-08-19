from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.kernel import KernelID
from ai.backend.common.data.entity.session import SESSION_ENTITY_TYPE, SessionID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.field.lookup import LookupFieldOwnerByKeyOpsAction
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.models.kernel.lookups import KernelSessionLookup


@dataclass(frozen=True)
class KernelIDKey(LookupKey):
    """The kernel a request names, which the session owning it is read from."""

    kernel_id: KernelID

    @override
    def kind(self) -> str:
        return "kernel_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"kernel_id": str(self.kernel_id)}


@dataclass
class LookupKernelOwnerAction(LookupFieldOwnerByKeyOpsAction[SessionID]):
    """Resolve a kernel's id into the session it runs under."""

    kernel_id: KernelID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SESSION_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_kernel_owner"

    @override
    def lookup_key(self) -> KernelIDKey:
        return KernelIDKey(kernel_id=self.kernel_id)

    @override
    def to_owner_lookup(self) -> KernelSessionLookup:
        return KernelSessionLookup(kernel_id=self.kernel_id)
