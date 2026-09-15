from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.session.types import SessionEntityData
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.session.searchers import SessionSearcher


@dataclass(frozen=True)
class GlobalSearchSessionsAction(SearchGlobalOpsAction[SessionRow, SessionEntityData]):
    """Page through every session."""

    searcher: SessionSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SessionEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_sessions"

    @override
    def to_searcher(self) -> SessionSearcher:
        return self.searcher
