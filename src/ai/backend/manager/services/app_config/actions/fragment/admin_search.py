from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.app_config import APP_CONFIG_FRAGMENT_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.app_config.types import AppConfigFragmentData
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.app_config_fragment.searchers import (
    AppConfigFragmentSearcher,
)


@dataclass
class AdminSearchAppConfigFragmentAction(
    SearchGlobalOpsAction[AppConfigFragmentRow, AppConfigFragmentData]
):
    """Super-admin path: search every fragment, across all scopes."""

    searcher: AppConfigFragmentSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return APP_CONFIG_FRAGMENT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "admin_search_app_config_fragments"

    @override
    def to_searcher(self) -> AppConfigFragmentSearcher:
        return self.searcher
