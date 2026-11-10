from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.session_group import SessionGroupEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.session_group.types import SessionGroupData
from ai.backend.manager.models.session_group.row import SessionGroupRow

__all__ = ("GlobalSearchSessionGroupsAction",)


@dataclass(frozen=True)
class GlobalSearchSessionGroupsAction(GlobalSearcherOpsAction[SessionGroupRow, SessionGroupData]):
    """Page through every session group in the installation, deployment groups included."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SessionGroupEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_session_groups"
