from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.session_group import SessionGroupEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import ScopedSearchOpsAction
from ai.backend.manager.data.session_group.types import SessionGroupData
from ai.backend.manager.models.session_group.row import SessionGroupRow

__all__ = ("ScopedSearchSessionGroupsAction",)


@dataclass(frozen=True)
class ScopedSearchSessionGroupsAction(ScopedSearchOpsAction[SessionGroupRow, SessionGroupData]):
    """Page through the session groups the named scopes reach, combined with OR.

    One scope the caller cannot see refuses the whole read.
    """

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SessionGroupEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_session_groups"
