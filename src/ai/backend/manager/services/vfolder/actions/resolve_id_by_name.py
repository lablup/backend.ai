from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action.base import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.vfolder.actions.base import VFolderAction


@dataclass
class ResolveIdByNameAction(VFolderAction):
    """Resolve a single vfolder name into its UUID.

    Legacy-only: this action exists solely to support the v1 CLI's
    name-keyed ``-v <vfolder-name>`` flag, which the modern UUID-keyed
    ``mount_ids`` surface bypasses entirely. Remove once the legacy
    name-keyed mount API is deprecated.

    No access scoping is performed inside the service — the caller is
    responsible for validating user access (and lifecycle state) of the
    resolved id in its own downstream flow.
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
class ResolveIdByNameActionResult(BaseActionResult):
    """Result of :class:`ResolveIdByNameAction`."""

    vfolder_id: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_id)
