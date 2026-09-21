from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
    SearchDeploymentRevisionPresetsInput,
)
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.repositories.model_card.types import AvailablePresetsSearchResult
from ai.backend.manager.services.model_card.actions.base import ModelCardSingleEntityAction


@dataclass
class AvailablePresetsAction(ModelCardSingleEntityAction):
    """Read the deployment revision presets that satisfy one model card's requirements."""

    search_input: SearchDeploymentRevisionPresetsInput

    @override
    @classmethod
    def action_name(cls) -> str:
        return "available_presets"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class AvailablePresetsActionResult:
    result: AvailablePresetsSearchResult
