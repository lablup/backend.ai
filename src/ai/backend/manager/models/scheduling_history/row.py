from __future__ import annotations

from datetime import datetime
from typing import override

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_history import DeploymentHistoryID
from ai.backend.common.data.entity.kernel import KernelID
from ai.backend.common.data.entity.kernel_scheduling_history import KernelSchedulingHistoryID
from ai.backend.common.data.entity.replica import ReplicaID
from ai.backend.common.data.entity.route_history import RouteHistoryID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.session_scheduling_history import SessionSchedulingHistoryID
from ai.backend.manager.data.deployment.types import (
    DeploymentHandlerCategory,
    RouteHandlerCategory,
)
from ai.backend.manager.data.session.types import (
    SchedulingResult,
    SubStepResult,
)
from ai.backend.manager.models.base import GUID, Base, PydanticListColumn, StrEnumType
from ai.backend.manager.models.mixins.history import ReconcileHistoryMixin

__all__ = (
    "DeploymentHistoryRow",
    "KernelSchedulingHistoryRow",
    "RouteHistoryRow",
    "SessionSchedulingHistoryRow",
)


class SessionSchedulingHistoryRow(ReconcileHistoryMixin, Base):
    __tablename__ = "session_scheduling_history"

    # Common columns (phase, from/to_status, result, error_code, message,
    # sub_steps, attempts, created_at, updated_at) come from the mixin; the id is
    # typed here and the merge rule below replaces the mixin's.
    id: Mapped[SessionSchedulingHistoryID] = mapped_column(
        "id",
        GUID(SessionSchedulingHistoryID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    session_id: Mapped[SessionID] = mapped_column(
        "session_id", GUID(SessionID), nullable=False, index=True
    )

    def records_an_attempt(self) -> bool:
        """Whether this record describes an attempt rather than a skip."""
        return self.result != SchedulingResult.SKIPPED

    @override
    def should_merge_with(self, other: SessionSchedulingHistoryRow) -> bool:
        """Check if a new entry should be merged with this one.

        Merge conditions:
        - Same phase, error_code, and to_status -> merge (increment attempts)
        - Both must describe an attempt, or both a skip
        - from_status and which attempt result (success/failure/give-up) do
          not affect the merge decision

        Skips are kept apart because ``attempts`` drives the give-up
        (deprioritization) classification, which may only count attempts a
        session really got.
        """
        return (
            self.phase == other.phase
            and self.error_code == other.error_code
            and self.to_status == other.to_status
            and self.records_an_attempt() == other.records_an_attempt()
        )


class KernelSchedulingHistoryRow(Base):
    __tablename__ = "kernel_scheduling_history"

    id: Mapped[KernelSchedulingHistoryID] = mapped_column(
        "id",
        GUID(KernelSchedulingHistoryID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    kernel_id: Mapped[KernelID] = mapped_column(
        "kernel_id", GUID(KernelID), nullable=False, index=True
    )
    session_id: Mapped[SessionID] = mapped_column(
        "session_id", GUID(SessionID), nullable=False, index=True
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

    def should_merge_with(self, new_row: KernelSchedulingHistoryRow) -> bool:
        """Check if a new entry should be merged with this one.

        Merge conditions:
        - Same phase, error_code, and to_status -> merge (increment attempts)
        - from_status and result (success/failure) do not affect merge decision
        """
        return (
            self.phase == new_row.phase
            and self.error_code == new_row.error_code
            and self.to_status == new_row.to_status
        )


class DeploymentHistoryRow(Base):
    __tablename__ = "deployment_history"

    id: Mapped[DeploymentHistoryID] = mapped_column(
        "id",
        GUID(DeploymentHistoryID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    deployment_id: Mapped[DeploymentID] = mapped_column(
        "deployment_id", GUID(DeploymentID), nullable=False, index=True
    )

    handler_category: Mapped[DeploymentHandlerCategory] = mapped_column(
        "handler_category",
        StrEnumType(DeploymentHandlerCategory),
        nullable=False,
        default=DeploymentHandlerCategory.LIFECYCLE,
        server_default=DeploymentHandlerCategory.LIFECYCLE.value,
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


class RouteHistoryRow(Base):
    __tablename__ = "route_history"

    id: Mapped[RouteHistoryID] = mapped_column(
        "id",
        GUID(RouteHistoryID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    route_id: Mapped[ReplicaID] = mapped_column(
        "route_id", GUID(ReplicaID), nullable=False, index=True
    )
    deployment_id: Mapped[DeploymentID] = mapped_column(
        "deployment_id", GUID(DeploymentID), nullable=False, index=True
    )

    category: Mapped[RouteHandlerCategory] = mapped_column(
        "category",
        StrEnumType(RouteHandlerCategory),
        nullable=False,
        server_default=sa.text("'lifecycle'"),
    )
    phase: Mapped[str] = mapped_column("phase", sa.String(length=64), nullable=False)
    from_status: Mapped[str | None] = mapped_column(
        "from_status", sa.String(length=64), nullable=True
    )
    to_status: Mapped[str | None] = mapped_column("to_status", sa.String(length=64), nullable=True)
    from_sub_status: Mapped[str | None] = mapped_column(
        "from_sub_status", sa.String(length=64), nullable=True
    )
    to_sub_status: Mapped[str | None] = mapped_column(
        "to_sub_status", sa.String(length=64), nullable=True
    )

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

    def should_merge_with(self, new_row: RouteHistoryRow) -> bool:
        return (
            self.category == new_row.category
            and self.phase == new_row.phase
            and self.error_code == new_row.error_code
        )
