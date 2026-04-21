"""RBAC-enforced v2 VFolder delete action.

Delete targets an existing vfolder by ID and uses
``SingleEntityActionProcessor`` with ``single_entity_rbac_validators``.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.vfolder.actions.base import (
    VFolderSingleEntityAction,
    VFolderSingleEntityActionResult,
)

# ---------------------------------------------------------------------------
# Delete v2 RBAC (single-entity — scope chain resolves project)
# ---------------------------------------------------------------------------


@dataclass
class DeleteVFolderV2RBACAction(VFolderSingleEntityAction):
    """Soft-delete a vfolder by ID with RBAC enforcement."""

    vfolder_id: uuid.UUID
    updater: Updater[VFolderRow]

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    def target_entity_id(self) -> str:
        return str(self.vfolder_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.VFOLDER,
            element_id=str(self.vfolder_id),
        )


@dataclass
class DeleteVFolderV2RBACActionResult(VFolderSingleEntityActionResult):
    vfolder_id: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_id)

    @override
    def target_entity_id(self) -> str:
        return str(self.vfolder_id)
