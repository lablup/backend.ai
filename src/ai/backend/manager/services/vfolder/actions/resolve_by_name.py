from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action.base import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.vfolder.actions.base import VFolderAction


@dataclass
class ResolveVFolderIdByNameAction(VFolderAction):
    """Resolve a single vfolder name into its UUID, scoped to the
    authenticated user.

    User context (``user_id`` / ``role`` / ``domain_name``) is read from
    :func:`current_user` inside the service, so the caller only needs to
    pass the name.
    """

    vfolder_name: str

    @override
    def entity_id(self) -> str | None:
        return self.vfolder_name

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class ResolveVFolderIdByNameActionResult(BaseActionResult):
    """Result of :class:`ResolveVFolderIdByNameAction`."""

    vfolder_id: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_id)
