"""Lookup implementations for the agent table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.types import AgentId
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.lookup import BulkDataLookup, DataLookup


@dataclass
class AgentNameLookup(DataLookup[AgentRow, AgentUUID]):
    """Resolves the operator-facing agent id into the agent it names.

    ``agents.id`` is the name an operator types; the entity id is the row's uuid.
    """

    agent_id: AgentId

    @override
    def row_class(self) -> type[AgentRow]:
        return AgentRow

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [lambda: AgentRow.id == self.agent_id]

    @override
    def to_entity_id(self, row: AgentRow) -> AgentUUID:
        return row.uuid


class AgentNamesLookup(BulkDataLookup[AgentId, AgentUUID]):
    """Resolves several operator-facing agent ids into the agents they name."""

    @override
    def build_query(self, keys: Sequence[AgentId]) -> sa.sql.Select[Any]:
        return sa.select(AgentRow.id, AgentRow.uuid).where(AgentRow.id.in_(keys))

    @override
    def to_entity_id(self, value: UUID) -> AgentUUID:
        return AgentUUID(value)
