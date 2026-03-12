from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class AgentResourceDrift:
    agent_id: str
    slot_name: str
    tracked: Decimal
    actual: Decimal
