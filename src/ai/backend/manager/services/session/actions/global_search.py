from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.session.types import SessionEntityData
from ai.backend.manager.models.session.row import SessionRow


@dataclass(frozen=True)
class GlobalSearchSessionsAction(GlobalSearcherOpsAction[SessionRow, SessionEntityData]):
    """Page through every session."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SessionEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_sessions"
