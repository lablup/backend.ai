from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import GetSingleEntityOpsAction
from ai.backend.manager.data.app_config.types import AppConfigFragmentData
from ai.backend.manager.models.app_config_fragment.queriers import (
    AppConfigFragmentQuerier,
)
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow


@dataclass
class GetAppConfigFragmentAction(
    GetSingleEntityOpsAction[AppConfigFragmentRow, AppConfigFragmentData]
):
    querier: AppConfigFragmentQuerier

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_app_config_fragment"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.querier.fragment_id

    @override
    def to_querier(self) -> AppConfigFragmentQuerier:
        return self.querier
