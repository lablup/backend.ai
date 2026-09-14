from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.idle_checker import IdleCheckerEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.idle_checker.types import IdleCheckerData
from ai.backend.manager.models.idle_checker.row import IdleCheckerRow
from ai.backend.manager.models.idle_checker.searchers import IdleCheckerSearcher


@dataclass(frozen=True)
class AdminSearchIdleCheckersAction(SearchGlobalOpsAction[IdleCheckerRow, IdleCheckerData]):
    """Page through the idle checker catalog."""

    searcher: IdleCheckerSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return IdleCheckerEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "admin_search_idle_checkers"

    @override
    def to_searcher(self) -> IdleCheckerSearcher:
        return self.searcher
