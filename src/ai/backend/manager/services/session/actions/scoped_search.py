"""Session search over the scopes sessions are reachable from."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import ScopedSearchOpsAction
from ai.backend.manager.data.session.types import SessionEntityData
from ai.backend.manager.models.session.row import SessionRow

__all__ = ("ScopedSearchSessionsAction",)


@dataclass(frozen=True)
class ScopedSearchSessionsAction(ScopedSearchOpsAction[SessionRow, SessionEntityData]):
    """Page through the sessions the named scopes reach, combined with OR.

    Every scope is authorized and every using entity must be readable before the read
    runs, so a caller reaching for one they cannot see is refused rather than served the rest.
    """

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SessionEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_sessions"
