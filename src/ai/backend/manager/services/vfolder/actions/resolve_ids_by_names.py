from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import override

from ai.backend.manager.actions.action.base import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.vfolder.actions.base import VFolderAction


@dataclass
class ResolveIdsByNamesAction(VFolderAction):
    """Resolve multiple vfolder names into their UUIDs in a single
    bulk lookup.

    Legacy-only: this action exists solely to support the v1 CLI's
    name-keyed ``-v <vfolder-name>`` flag, which the modern UUID-keyed
    ``mount_ids`` surface bypasses entirely. Remove once the legacy
    name-keyed mount API is deprecated.

    No access scoping is performed inside the service — the caller is
    responsible for validating user access (and lifecycle state) of the
    resolved ids in its own downstream flow.
    """

    vfolder_names: Sequence[str]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class ResolveIdsByNamesActionResult(BaseActionResult):
    """Result of :class:`ResolveIdsByNamesAction` — a ``name → UUID`` map
    covering every requested name.
    """

    name_to_id: dict[str, uuid.UUID] = field(default_factory=dict)

    @override
    def entity_id(self) -> str | None:
        return None
