from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment_revision_preset.types import DeploymentRevisionPresetData
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.deployment_revision_preset.actions.base import (
    DeploymentRevisionPresetAction,
)


@dataclass
class UpdateDeploymentRevisionPresetAction(DeploymentRevisionPresetAction):
    id: UUID
    updater: Updater[DeploymentRevisionPresetRow]

    @override
    def entity_id(self) -> str | None:
        return str(self.id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdateDeploymentRevisionPresetActionResult(BaseActionResult):
    preset: DeploymentRevisionPresetData

    @override
    def entity_id(self) -> str | None:
        return str(self.preset.id)
