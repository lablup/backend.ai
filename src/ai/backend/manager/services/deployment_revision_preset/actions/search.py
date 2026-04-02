from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment_revision_preset.types import DeploymentRevisionPresetData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.deployment_revision_preset.actions.base import (
    DeploymentRevisionPresetAction,
)


@dataclass
class SearchDeploymentRevisionPresetsAction(DeploymentRevisionPresetAction):
    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class SearchDeploymentRevisionPresetsActionResult(BaseActionResult):
    items: list[DeploymentRevisionPresetData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
