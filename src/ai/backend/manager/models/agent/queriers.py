"""DataQuerier implementations for the agent table."""

from __future__ import annotations

from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.manager.data.agent.types import AgentData
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.specs.querier import BulkEntityQuerier


class BulkAgentQuerier(BulkEntityQuerier[AgentRow, AgentData]):
    """The agents the caller named; the slot rows are a field read of their own."""

    @override
    def row_class(self) -> type[AgentRow]:
        return AgentRow

    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return AgentRow.uuid

    @override
    def to_data(self, row: AgentRow) -> AgentData:
        return row.to_data()
