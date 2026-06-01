"""Resolve a vfolder row by UUID without permission filtering.

Used by the REST middleware when the path parameter is a UUID — permission
evaluation is delegated to the downstream RBAC validator on the actual action
(e.g., update_vfolder_attribute).
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.manager.actions.action.base import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.vfolder.actions.base import VFolderAction


@dataclass
class GetVFolderLegacyRowAction(VFolderAction):
    vfolder_uuid: VFolderUUID

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_uuid)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetVFolderLegacyRowActionResult(BaseActionResult):
    row: Mapping[str, Any]

    @override
    def entity_id(self) -> str | None:
        return str(self.row.get("id")) if self.row else None
