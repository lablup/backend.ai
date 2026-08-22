"""Resolution of a vfolder's name into the folder it names."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.vfolder import VFOLDER_ENTITY_TYPE, VFolderUUID
from ai.backend.manager.actions.v2.lookup.base import (
    BaseLookupAction,
    BaseLookupActionResult,
    LookupKey,
)


@dataclass(frozen=True)
class VFolderNameKey(LookupKey):
    """The name a caller passes instead of the folder's id."""

    vfolder_name: str

    @override
    def kind(self) -> str:
        return "vfolder_name"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"vfolder_name": self.vfolder_name}


@dataclass
class LookupVFolderAction(BaseLookupAction):
    """Resolve a folder name into the folder it names.

    Legacy-only: the v1 CLI accepts ``-v <vfolder-name>`` where the modern
    surface passes ids. Names are not unique across owners, so the row a
    duplicate name resolves to is arbitrary.
    """

    vfolder_name: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return VFOLDER_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_vfolder"

    @override
    def lookup_key(self) -> VFolderNameKey:
        return VFolderNameKey(vfolder_name=self.vfolder_name)


@dataclass
class LookupVFolderActionResult(BaseLookupActionResult):
    vfolder_uuid: VFolderUUID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.vfolder_uuid
