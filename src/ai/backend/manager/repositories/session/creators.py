"""Creator specs for session entities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.repositories.base.creator import CreatorSpec


@dataclass
class SessionRowCreatorSpec(CreatorSpec[SessionRow]):
    """CreatorSpec that wraps a pre-built SessionRow.

    This spec is designed for retrofitting existing code that already builds
    SessionRow instances. It simply returns the provided row in build_row().

    For scope information needed by RBACEntityCreator, use the row's user_uuid
    field as the scope_id with ScopeType.USER.
    """

    row: SessionRow

    @override
    def build_row(self) -> SessionRow:
        return self.row
