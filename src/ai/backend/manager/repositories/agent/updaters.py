"""UpdaterSpec implementations for agent repository."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, override

from ai.backend.manager.models.agent import AgentRow, AgentStatus
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState


@dataclass
class AgentStatusUpdaterSpec(UpdaterSpec[AgentRow]):
    """UpdaterSpec for agent status updates."""

    status: AgentStatus
    status_changed: datetime
    lost_at: OptionalState[datetime] = field(default_factory=lambda: OptionalState.nop())

    @property
    @override
    def row_class(self) -> type[AgentRow]:
        return AgentRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {
            "status": self.status,
            "status_changed": self.status_changed,
        }
        self.lost_at.update_dict(to_update, "lost_at")
        return to_update
