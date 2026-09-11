"""DataLookup implementations for the resource slot repository."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.data.entity.agent_resource import AgentResourceID
from ai.backend.common.data.entity.resource_slot import (
    ResourceSlotTypeEntityType,
    ResourceSlotTypeUUID,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.resource_slot.row import AgentResourceRow, ResourceSlotTypeRow
from ai.backend.manager.models.specs.lookup import DataLookup, FieldOwnerLookup


@dataclass
class ResourceSlotTypeLookup(DataLookup[ResourceSlotTypeRow, ResourceSlotTypeUUID]):
    """Resolves a slot name into the type it names."""

    slot_name: str

    @override
    def row_class(self) -> type[ResourceSlotTypeRow]:
        return ResourceSlotTypeRow

    @override
    def entity_type(self) -> EntityType:
        return ResourceSlotTypeEntityType()

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [lambda: ResourceSlotTypeRow.slot_name == self.slot_name]

    @override
    def to_entity_id(self, row: ResourceSlotTypeRow) -> ResourceSlotTypeUUID:
        return row.uuid


class AgentResourceOwnerLookup(FieldOwnerLookup[AgentResourceID, AgentUUID]):
    """The agent a slot row belongs to; the row names the agent by ``agents.id``."""

    @override
    def build_query(
        self, field_ids: Sequence[AgentResourceID]
    ) -> sa.sql.Select[tuple[AgentResourceID, AgentUUID]]:
        return (
            sa.select(AgentResourceRow.id, AgentRow.uuid)
            .join(AgentRow, AgentRow.id == AgentResourceRow.agent_id)
            .where(AgentResourceRow.id.in_(field_ids))
        )

    @override
    def to_entity_id(self, value: UUID) -> AgentUUID:
        return AgentUUID(value)
