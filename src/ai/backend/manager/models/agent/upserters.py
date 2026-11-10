"""Upsert specs for agents."""

from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.agent.types import AgentHeartbeatUpsert
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter


@dataclass
class AgentHeartbeatUpserter(EntityUpserter[AgentRow, AgentUUID]):
    """Registers an agent from its heartbeat, created in the resource group resolved for it.

    Conflict key: id. On conflict the reported state is updated and the group is kept.
    """

    upsert_data: AgentHeartbeatUpsert
    resource_group_id: ResourceGroupID
    resource_group_name: str

    @override
    def entity_id(self, row: AgentRow) -> AgentUUID:
        return AgentUUID(row.uuid)

    @override
    def created_in(self, row: AgentRow) -> Collection[EntityIdentifier]:
        return (ResourceGroupID(row.resource_group_id),)

    @override
    def row_class(self) -> type[AgentRow]:
        return AgentRow

    @override
    def index_elements(self) -> list[str]:
        return ["id"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {
            **self.upsert_data.insert_fields,
            "scaling_group": self.resource_group_name,
            "resource_group_id": self.resource_group_id,
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        return dict(self.upsert_data.update_fields)

    @override
    def to_data(self, row: AgentRow) -> AgentUUID:
        return AgentUUID(row.uuid)
