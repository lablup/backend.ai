"""Lookup implementations for the session table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.entity.session import SessionID
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.specs.lookup import DataLookup


@dataclass
class SessionNameOfUserLookup(DataLookup[SessionRow, SessionID]):
    """Resolves a session's name within its owner into the session it names.

    ``ix_sessions_unique_name_per_user_nonterminal`` is what makes the pair a key: a name
    is unique per user while the session has not reached a terminal status, and the
    terminal ones are excluded here for the same reason.
    """

    user_uuid: UUID
    name: str

    @override
    def row_class(self) -> type[SessionRow]:
        return SessionRow

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [
            lambda: SessionRow.user_uuid == self.user_uuid,
            lambda: SessionRow.name == self.name,
            lambda: SessionRow.status.not_in(SessionStatus.terminal_statuses()),
        ]

    @override
    def to_entity_id(self, row: SessionRow) -> SessionID:
        return SessionID(row.id)
