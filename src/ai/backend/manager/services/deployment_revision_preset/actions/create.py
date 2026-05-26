from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment_revision_preset.types import DeploymentRevisionPresetData
from ai.backend.manager.repositories.deployment_revision_preset.creators import (
    DeploymentRevisionPresetCreatorSpec,
    PresetResourceSlotDependentCreatorSpec,
)
from ai.backend.manager.services.deployment_revision_preset.actions.base import (
    DeploymentRevisionPresetAction,
)


@dataclass
class CreateDeploymentRevisionPresetAction(DeploymentRevisionPresetAction):
    creator_spec: DeploymentRevisionPresetCreatorSpec
    resource_slot_specs: list[PresetResourceSlotDependentCreatorSpec]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateDeploymentRevisionPresetActionResult(BaseActionResult):
    preset: DeploymentRevisionPresetData

    @override
    def entity_id(self) -> str | None:
        return str(self.preset.id)
