from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.session.types import SessionSchedulingHistoryData
from ai.backend.manager.models.scheduling_history.row import SessionSchedulingHistoryRow


@dataclass(frozen=True)
class SearchSessionHistoryAction(
    GlobalSearcherOpsAction[SessionSchedulingHistoryRow, SessionSchedulingHistoryData]
):
    """Page through every session scheduling history row."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SessionEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_session_history"
