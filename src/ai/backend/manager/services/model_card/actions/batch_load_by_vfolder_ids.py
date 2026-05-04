from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.manager.actions.action.base import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.model_card.types import ModelCardData
from ai.backend.manager.services.model_card.actions.base import ModelCardAction


@dataclass
class BatchLoadModelCardsByVFolderIdsAction(ModelCardAction):
    """Batch fetch model cards grouped by their linked vfolder ID.

    Used by the GraphQL ``VFolderGQL.model_cards`` resolver (DataLoader) to
    avoid N+1 fetches when many vfolders are listed. The caller already
    authorized vfolder visibility; this action does no scope filtering.

    A single vfolder may back multiple cards (the unique constraint is on
    ``(name, domain, project)``), so the result groups cards per vfolder.
    """

    vfolder_ids: list[VFolderUUID]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class BatchLoadModelCardsByVFolderIdsActionResult(BaseActionResult):
    """Result of :class:`BatchLoadModelCardsByVFolderIdsAction`.

    ``data`` is the same length and order as the input ``vfolder_ids``;
    each entry is the (possibly empty) list of cards backed by that vfolder,
    most-recently-created first.
    """

    data: list[list[ModelCardData]]

    @override
    def entity_id(self) -> str | None:
        return None
