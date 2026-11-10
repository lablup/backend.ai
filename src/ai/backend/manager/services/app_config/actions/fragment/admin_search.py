from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.app_config_fragment import AppConfigFragmentEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.app_config.types import AppConfigFragmentData
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow


@dataclass(frozen=True)
class AdminSearchAppConfigFragmentAction(
    GlobalSearcherOpsAction[AppConfigFragmentRow, AppConfigFragmentData]
):
    """Super-admin path: search every fragment, across all scopes."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return AppConfigFragmentEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "admin_search_app_config_fragments"
