"""UpdaterSpec implementations for session repository."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState


@dataclass
class SessionUpdaterSpec(UpdaterSpec[SessionRow]):
    """UpdaterSpec for session updates."""

    name: OptionalState[str] = field(default_factory=OptionalState.nop)
    priority: OptionalState[int] = field(default_factory=OptionalState.nop)

    @property
    @override
    def row_class(self) -> type[SessionRow]:
        return SessionRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.priority.update_dict(to_update, "priority")
        return to_update
