from dataclasses import dataclass, field
from datetime import datetime
from typing import override

from ai.backend.manager.models.agent import AgentStatus
from ai.backend.manager.types import OptionalState, PartialModifier


@dataclass
class AgentStatusModifier(PartialModifier):
    status: AgentStatus
    status_changed: datetime
    lost_at: OptionalState[datetime] = field(default_factory=lambda: OptionalState.nop())

    @override
    def fields_to_update(self) -> dict:
        to_update = {
            "status": self.status,
            "status_changed": self.status_changed,
        }
        self.lost_at.update_dict(to_update, "lost_at")
        return to_update
