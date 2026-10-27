"""Upsert specs of the resource slot tables."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, override

from ai.backend.common.data.entity.agent import AgentUUID
<<<<<<< HEAD
from ai.backend.manager.data.resource_slot.types import AgentResourceData
from ai.backend.manager.models.resource_slot.row import AgentResourceRow
=======
from ai.backend.common.data.entity.resource_slot import ResourceSlotTypeUUID
from ai.backend.common.types import SlotTypes
from ai.backend.manager.data.resource_slot.types import AgentResourceData, ResourceSlotTypeData
from ai.backend.manager.errors.repository import ForeignKeyViolationError
from ai.backend.manager.errors.resource_slot import ResourceSlotTypeNotFound
from ai.backend.manager.models.resource_slot.row import AgentResourceRow, ResourceSlotTypeRow
>>>>>>> c8c1c108 (fix(BA-8140): name the unregistered slot type when a heartbeat fails on it (#16094))
from ai.backend.manager.models.resource_slot.searchable_fields import (
    AgentResourceSearchableFields,
)
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
        return (
            IntegrityErrorCheck(
                violation_type=ForeignKeyViolationError,
                constraint_name="fk_agent_resources_slot_name_resource_slot_types",
                error=ResourceSlotTypeNotFound(
                    f"Resource slot type '{self.slot_name}' reported by agent '{self.agent_id}'"
                    " is not registered. Register it with"
                    " `./bai resource-slot slot-type create`."
                ),
            ),
        )

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
        return AgentResourceSearchableFields.own.to_data(row)
