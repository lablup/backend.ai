from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
    SearchDeploymentRevisionPresetsInput,
)
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.repositories.model_card.types import AvailablePresetsSearchResult
from ai.backend.manager.services.model_card.actions.base import ModelCardAction


@dataclass
class AvailablePresetsAction(ModelCardAction):
    model_card_id: UUID
    search_input: SearchDeploymentRevisionPresetsInput

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def entity_id(self) -> str | None:
        return str(self.model_card_id)


@dataclass
class AvailablePresetsActionResult(BaseActionResult):
    result: AvailablePresetsSearchResult

    @override
    def entity_id(self) -> str | None:
        return None
