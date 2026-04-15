from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.deployment.actions.base import DeploymentBaseAction


@dataclass(frozen=True)
class SyncModelDefinitionsAction(DeploymentBaseAction):
    """Action to sync model_definition from vfolder storage for all deployment revisions."""

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass(frozen=True)
class SyncModelDefinitionsActionResult(BaseActionResult):
    updated: int
    failed: int

    @override
    def entity_id(self) -> str | None:
        return None
