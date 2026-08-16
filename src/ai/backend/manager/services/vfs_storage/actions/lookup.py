from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.vfs_storage import VFS_STORAGE_ENTITY_TYPE
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.actions.v2.ops.base import LookupEntityOpsAction
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.models.vfs_storage.row import VFSStorageRow
from ai.backend.manager.repositories.vfs_storage.lookups import VFSStorageLookup


@dataclass(frozen=True)
class VFSStorageNameKey(LookupKey):
    """The registration name a caller passes instead of the storage's id."""

    name: str

    @override
    def kind(self) -> str:
        return "vfs_storage_name"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name}


@dataclass
class LookupVFSStorageAction(LookupEntityOpsAction[VFSStorageRow, VFSStorageData]):
    """Resolve a VFS storage name into the storage it names.

    Split out of the read: the old ``get`` branched on which key the caller
    supplied, which is the shape the lookup family exists to absorb.
    """

    name: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return VFS_STORAGE_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_vfs_storage"

    @override
    def lookup_key(self) -> VFSStorageNameKey:
        return VFSStorageNameKey(name=self.name)

    @override
    def to_lookup(self) -> VFSStorageLookup:
        return VFSStorageLookup(name=self.name)
