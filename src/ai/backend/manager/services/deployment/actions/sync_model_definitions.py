from dataclasses import dataclass, field
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction, BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType


@dataclass(frozen=True)
class RevisionSyncStatus:
    revision_id: UUID
    success: bool
    reason: str | None = None


@dataclass(frozen=True)
class SyncModelDefinitionsAction(BaseAction):
    """Action to sync model_definition from vfolder storage for all deployment revisions."""

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.MODEL_DEPLOYMENT

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass(frozen=True)
class SyncModelDefinitionsActionResult(BaseActionResult):
    results: list[RevisionSyncStatus] = field(default_factory=list)

    @override
    def entity_id(self) -> str | None:
        return None
