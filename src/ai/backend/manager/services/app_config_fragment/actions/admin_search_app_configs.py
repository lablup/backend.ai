from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_fragment.types import AppConfigData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.app_config_fragment.actions.base import AppConfigFragmentAction


@dataclass
class AdminSearchAppConfigsAction(AppConfigFragmentAction):
    """Cross-user merged-view search(admin only)."""

    querier: BatchQuerier

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class AdminSearchAppConfigsActionResult(BaseActionResult):
    items: list[AppConfigData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
