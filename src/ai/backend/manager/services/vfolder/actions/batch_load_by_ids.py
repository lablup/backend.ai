from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action.base import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.services.vfolder.actions.base import VFolderAction


@dataclass
class BatchLoadVFoldersByIdsAction(VFolderAction):
    """Batch fetch vfolders by IDs.

    Used by GraphQL field resolvers (DataLoader) to load vfolders that are
    referenced from other entities (e.g. ``ModelCardGQL.vfolder``). This is
    deliberately distinct from the admin search action so that audit logs do
    not record cross-entity reference resolution as an admin search.

    The caller (an upper layer that already authorized access to the parent
    entity) is responsible for ensuring that exposing the requested vfolders
    is acceptable. The action itself performs no scope filtering.
    """

    ids: list[uuid.UUID]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class BatchLoadVFoldersByIdsActionResult(BaseActionResult):
    """Result of :class:`BatchLoadVFoldersByIdsAction`.

    ``data`` is the same length and order as the input ids; entries that
    were not found are ``None``.
    """

    data: list[VFolderData | None]

    @override
    def entity_id(self) -> str | None:
        return None
