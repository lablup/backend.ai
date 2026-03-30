"""Upserter specs for resource slot repository upsert operations."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, override

from ai.backend.manager.models.resource_slot import AgentResourceRow
from ai.backend.manager.repositories.base import UpserterSpec


@dataclass
class AgentResourceUpserterSpec(UpserterSpec[AgentResourceRow]):
    """Upserter spec for AgentResourceRow.

    Unique constraint: (agent_id, slot_name) — composite primary key.

    On INSERT: sets capacity (and optionally used).
    On CONFLICT UPDATE: only updates capacity.
    """

    agent_id: str
    slot_name: str
    capacity: Decimal
    used: Decimal | None = None

    @property
    @override
    def row_class(self) -> type[AgentResourceRow]:
        return AgentResourceRow

    @override
    def build_insert_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {
            "agent_id": self.agent_id,
            "slot_name": self.slot_name,
            "capacity": self.capacity,
        }
        if self.used is not None:
            values["used"] = self.used
        return values

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {"capacity": self.capacity}
