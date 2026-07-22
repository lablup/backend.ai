from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_definition.types import AppConfigDefinitionData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.app_config_definition.actions.base import (
    AppConfigDefinitionGlobalAction,
)


@dataclass
class SearchAppConfigDefinitionsAction(AppConfigDefinitionGlobalAction):
    """Super-admin path: search every registered config definition."""

    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class SearchAppConfigDefinitionsActionResult(BaseActionResult):
    data: list[AppConfigDefinitionData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
