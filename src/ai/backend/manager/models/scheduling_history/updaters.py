"""Update specs for the deployment history table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

from ai.backend.manager.data.deployment.types import DeploymentHistoryData
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.scheduling_history.conditions import DeploymentHistoryConditions
from ai.backend.manager.models.scheduling_history.row import DeploymentHistoryRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataBatchUpdater


@dataclass
class DeploymentHistoryAttemptUpdater(
    DataBatchUpdater[DeploymentHistoryRow, DeploymentHistoryData]
):
    """Counts a repeated transition onto the history rows it recurs on."""

    history_ids: Sequence[UUID]

    @property
    @override
    def row_class(self) -> type[DeploymentHistoryRow]:
        return DeploymentHistoryRow

    @override
    def conditions(self) -> list[QueryCondition]:
        return [DeploymentHistoryConditions.by_ids(list(self.history_ids))]

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        return {"attempts": DeploymentHistoryRow.attempts + 1}

    @override
    def to_data(self, row: DeploymentHistoryRow) -> DeploymentHistoryData:
        return row.to_data()
