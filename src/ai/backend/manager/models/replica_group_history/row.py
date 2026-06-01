from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.manager.data.deployment.types import (
    ReplicaGroupHandlerCategory,
    ReplicaGroupHistoryData,
)
from ai.backend.manager.data.session.types import SchedulingResult, SubStepResult
from ai.backend.manager.models.base import GUID, Base, PydanticListColumn, StrEnumType

__all__ = ("ReplicaGroupHistoryRow",)


class ReplicaGroupHistoryRow(Base):  # type: ignore[misc]
    __tablename__ = "replica_group_history"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
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
    phase: Mapped[str] = mapped_column("phase", sa.String(length=64), nullable=False)
    from_status: Mapped[str | None] = mapped_column(
        "from_status", sa.String(length=64), nullable=True
    )
    to_status: Mapped[str | None] = mapped_column("to_status", sa.String(length=64), nullable=True)

    result: Mapped[str] = mapped_column("result", sa.String(length=32), nullable=False)
    error_code: Mapped[str | None] = mapped_column(
        "error_code", sa.String(length=128), nullable=True
    )
    message: Mapped[str] = mapped_column("message", sa.Text, nullable=False)

    sub_steps: Mapped[list[SubStepResult]] = mapped_column(
        "sub_steps",
        PydanticListColumn(SubStepResult),
        nullable=False,
        server_default=sa.text("'[]'::jsonb"),
    )

    attempts: Mapped[int] = mapped_column("attempts", sa.Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        default=sa.func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at",
        sa.DateTime(timezone=True),
        nullable=False,
        default=sa.func.now(),
        onupdate=sa.func.now(),
    )

    def should_merge_with(self, new_row: ReplicaGroupHistoryRow) -> bool:
        return (
            self.category == new_row.category
            and self.phase == new_row.phase
            and self.error_code == new_row.error_code
        )

    def to_data(self) -> ReplicaGroupHistoryData:
        return ReplicaGroupHistoryData(
            id=self.id,
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
