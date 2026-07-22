from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config_allow_list.types import AppConfigAllowListData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.app_config_allow_list.actions.base import (
    AppConfigAllowListGlobalAction,
)


@dataclass
class SearchAppConfigAllowListAction(AppConfigAllowListGlobalAction):
    """Super-admin path: search every allow-list entry, across all scope types."""

    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class SearchAppConfigAllowListActionResult(BaseActionResult):
    data: list[AppConfigAllowListData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
