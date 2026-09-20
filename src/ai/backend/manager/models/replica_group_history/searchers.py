"""List-read spec for the replica-group history table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.deployment.types import ReplicaGroupHistoryData
from ai.backend.manager.models.replica_group_history.row import ReplicaGroupHistoryRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class ReplicaGroupHistorySearcher(Searcher[ReplicaGroupHistoryRow, ReplicaGroupHistoryData]):
    """Replica-group history rows matching the conditions."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ReplicaGroupHistoryRow)

    @override
    def to_data(self, row: ReplicaGroupHistoryRow) -> ReplicaGroupHistoryData:
        return row.to_data()
