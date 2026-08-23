"""Creator specs for the replica group history table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.replica_group import ReplicaGroupID
from ai.backend.common.data.entity.replica_group_history import ReplicaGroupHistoryID
from ai.backend.manager.data.deployment.types import (
    ReplicaGroupHandlerCategory,
    ReplicaGroupHistoryData,
)
from ai.backend.manager.data.session.types import SchedulingResult, SubStepResult
from ai.backend.manager.models.replica_group_history.row import ReplicaGroupHistoryRow
from ai.backend.manager.models.specs.creator import FieldCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class ReplicaGroupHistoryCreator(
    FieldCreator[DeploymentID, ReplicaGroupHistoryRow, ReplicaGroupHistoryData]
):
    """Records one transition of a replica group, under its deployment.

    ``from_status``/``to_status`` are plain strings because the meaning differs
    by category (scaling status vs lifecycle); the caller stringifies the right enum.
    """

    replica_group_id: ReplicaGroupID
    category: ReplicaGroupHandlerCategory
    phase: str
    result: SchedulingResult
    message: str
    from_status: str | None = None
    to_status: str | None = None
    error_code: str | None = None
    sub_steps: list[SubStepResult] = field(default_factory=list)

    @override
    def field_id(self, row: ReplicaGroupHistoryRow) -> ReplicaGroupHistoryID:
        return ReplicaGroupHistoryID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self, owner_id: DeploymentID) -> ReplicaGroupHistoryRow:
        return ReplicaGroupHistoryRow(
            replica_group_id=self.replica_group_id,
            deployment_id=owner_id,
            category=self.category,
            phase=self.phase,
            from_status=self.from_status,
            to_status=self.to_status,
            result=str(self.result),
            error_code=self.error_code,
            message=self.message,
            sub_steps=self.sub_steps,
            attempts=1,
        )

    @override
    def to_data(self, row: ReplicaGroupHistoryRow) -> ReplicaGroupHistoryData:
        return row.to_data()
