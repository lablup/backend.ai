from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment_revision_preset.types import DeploymentRevisionPresetData
from ai.backend.manager.services.deployment_revision_preset.actions.base import (
    DeploymentRevisionPresetAction,
)


@dataclass
class DeleteDeploymentRevisionPresetAction(DeploymentRevisionPresetAction):
    id: UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DeleteDeploymentRevisionPresetActionResult(BaseActionResult):
    preset: DeploymentRevisionPresetData

    @override
    def entity_id(self) -> str | None:
        return str(self.preset.id)
