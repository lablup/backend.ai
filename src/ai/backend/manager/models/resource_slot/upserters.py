"""Upsert specs of the resource slot tables."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, override

from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.manager.data.resource_slot.types import AgentResourceData
from ai.backend.manager.models.resource_slot.row import AgentResourceRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import FieldUpserter


@dataclass
class AgentResourceUpserter(FieldUpserter[AgentUUID, AgentResourceRow, AgentResourceData]):
    """One slot's capacity on one agent.

    The insert carries the used amount; a conflict retunes the capacity alone, so an
    agent re-reporting its slots does not disturb what is held on them.
    """

    agent_id: str
    slot_name: str
    capacity: Decimal
    used: Decimal | None = None

    @override
    def row_class(self) -> type[AgentResourceRow]:
        return AgentResourceRow

    @override
    def index_elements(self) -> list[str]:
        return ["agent_id", "slot_name"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self, owner_id: AgentUUID) -> dict[str, Any]:
        values: dict[str, Any] = {
            "agent_id": self.agent_id,
            "agent_uuid": owner_id,
            "slot_name": self.slot_name,
            "capacity": self.capacity,
        }
        if self.used is not None:
            values["used"] = self.used
        return values

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {"capacity": self.capacity}

    @override
    def to_data(self, row: AgentResourceRow) -> AgentResourceData:
        return row.to_data()
