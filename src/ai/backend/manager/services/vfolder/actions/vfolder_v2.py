"""V2 vfolder action definitions."""

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.services.vfolder.actions.base import VFolderAction


@dataclass
class DeleteVFolderV2Action(VFolderAction):
    """Soft-delete a vfolder by ID with RBAC enforcement."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_vfolder_v2"


@dataclass
class DeleteVFolderV2ActionResult:
    vfolder: VFolderData


@dataclass
class PurgeVFolderV2Action(VFolderAction):
    """Permanently purge a vfolder by ID with RBAC enforcement.

    By default the call is rejected when any model card references the
    vfolder. Set ``cascade_model_card=True`` to also remove the linked
    model card row(s) atomically.

    By default the call is also rejected when the vfolder is mounted by a
    live session, referenced by an active model-service endpoint, or not in
    a purgable status. Set ``force=True`` to bypass those in-use guards.
    """

    cascade_model_card: bool = False
    force: bool = False

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_vfolder_v2"


@dataclass
class PurgeVFolderV2ActionResult:
    vfolder_id: uuid.UUID
