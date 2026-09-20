"""List-read spec for the agent table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.agent.types import AgentData
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class AgentSearcher(Searcher[AgentRow, AgentData]):
    """Agents matching the conditions; the slot rows are a field read of their own."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(AgentRow)

    @override
    def to_data(self, row: AgentRow) -> AgentData:
        return row.to_data()
