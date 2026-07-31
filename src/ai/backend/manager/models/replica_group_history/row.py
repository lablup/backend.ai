from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.common.identifier.replica_group_history import ReplicaGroupHistoryID
from ai.backend.manager.data.deployment.types import (
    ReplicaGroupHandlerCategory,
    ReplicaGroupHistoryData,
)
from ai.backend.manager.data.session.types import SchedulingResult
from ai.backend.manager.models.base import GUID, Base, StrEnumType
from ai.backend.manager.models.mixins.history import ReconcileHistoryMixin

__all__ = ("ReplicaGroupHistoryRow",)


class ReplicaGroupHistoryRow(ReconcileHistoryMixin, Base):  # type: ignore[misc]
    __tablename__ = "replica_group_history"

    # Common columns (id, phase, from/to_status, result, error_code, message,
    # attempts, created_at, updated_at) and ``should_merge_with`` come from the mixin.
    replica_group_id: Mapped[ReplicaGroupID] = mapped_column(
        "replica_group_id", GUID(ReplicaGroupID), nullable=False, index=True
    )
    deployment_id: Mapped[DeploymentID] = mapped_column(
        "deployment_id", GUID(DeploymentID), nullable=False, index=True
    )

    category: Mapped[ReplicaGroupHandlerCategory] = mapped_column(
        "category",
        StrEnumType(ReplicaGroupHandlerCategory),
        nullable=False,
        server_default=ReplicaGroupHandlerCategory.LIFECYCLE.value,
    )

    def to_data(self) -> ReplicaGroupHistoryData:
        return ReplicaGroupHistoryData(
            id=ReplicaGroupHistoryID(self.id),
            replica_group_id=self.replica_group_id,
            deployment_id=self.deployment_id,
            category=self.category,
            phase=self.phase,
            from_status=self.from_status,
            to_status=self.to_status,
            result=SchedulingResult(self.result),
            error_code=self.error_code,
            message=self.message,
            sub_steps=self.sub_steps,
            attempts=self.attempts,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
