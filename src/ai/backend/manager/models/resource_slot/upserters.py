"""Upsert specs of the resource slot tables."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.data.entity.resource_slot import ResourceSlotTypeUUID
from ai.backend.common.types import SlotTypes
from ai.backend.manager.data.resource_slot.types import AgentResourceData, ResourceSlotTypeData
from ai.backend.manager.errors.repository import ForeignKeyViolationError
from ai.backend.manager.errors.resource_slot import ResourceSlotTypeNotFound
from ai.backend.manager.models.resource_slot.row import AgentResourceRow, ResourceSlotTypeRow
from ai.backend.manager.models.resource_slot.searchable_fields import (
    AgentResourceSearchableFields,
    ResourceSlotTypeSearchableFields,
)
from ai.backend.manager.models.resource_slot.types import NumberFormat
from ai.backend.manager.models.specs.created_in import CreatedInPublic
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter, FieldUpserter


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


@dataclass
class ResourceSlotTypeUpserter(
    CreatedInPublic[ResourceSlotTypeRow],
    EntityUpserter[ResourceSlotTypeRow, ResourceSlotTypeData],
):
    """A resource slot type under its stated uuid, the conflict key. ``slot_name`` is
    written on insert only: five tables refer to the slot by it."""

    uuid: ResourceSlotTypeUUID
    slot_name: str
    slot_type: SlotTypes
    required: bool
    enabled: bool
    display_name: str
    description: str
    display_unit: str
    display_icon: str
    number_format: NumberFormat
    rank: int

    @override
    def entity_id(self, row: ResourceSlotTypeRow) -> ResourceSlotTypeUUID:
        return ResourceSlotTypeUUID(row.uuid)

    @override
    def row_class(self) -> type[ResourceSlotTypeRow]:
        return ResourceSlotTypeRow

    @override
    def index_elements(self) -> list[str]:
        return ["uuid"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {"uuid": self.uuid, "slot_name": self.slot_name, **self._values()}

    @override
    def build_update_values(self) -> dict[str, Any]:
        """``updated_at`` is set here: ``ON CONFLICT DO UPDATE`` bypasses the ORM's
        ``onupdate``."""
        return {**self._values(), "updated_at": sa.func.now()}

    def _values(self) -> dict[str, Any]:
        return {
            "slot_type": self.slot_type.value,
            "required": self.required,
            "enabled": self.enabled,
            "display_name": self.display_name,
            "description": self.description,
            "display_unit": self.display_unit,
            "display_icon": self.display_icon,
            "number_format": self.number_format,
            "rank": self.rank,
        }

    @override
    def to_data(self, row: ResourceSlotTypeRow) -> ResourceSlotTypeData:
        return ResourceSlotTypeSearchableFields.own.to_data(row)
