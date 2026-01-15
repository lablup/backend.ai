from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.model_deployment.types import ModelDeploymentStatus
from ai.backend.common.types import KernelId, SessionId
from ai.backend.manager.data.deployment.types import (
    DeploymentHistoryData,
    RouteHistoryData,
    RouteStatus,
)
from ai.backend.manager.data.kernel.types import (
    KernelSchedulingHistoryData,
    KernelSchedulingPhase,
)
from ai.backend.manager.data.session.types import (
    SchedulingResult,
    SessionSchedulingHistoryData,
    SessionStatus,
    SubStepResult,
)
from ai.backend.manager.models.base import GUID, Base, PydanticListColumn

__all__ = (
    "DeploymentHistoryRow",
    "KernelSchedulingHistoryRow",
    "RouteHistoryRow",
    "SessionSchedulingHistoryRow",
)


class SessionSchedulingHistoryRow(Base):
    __tablename__ = "session_scheduling_history"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    session_id: Mapped[uuid.UUID] = mapped_column("session_id", GUID, nullable=False, index=True)

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

    def should_merge_with(self, new_row: SessionSchedulingHistoryRow) -> bool:
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

    def to_data(self) -> SessionSchedulingHistoryData:
        return SessionSchedulingHistoryData(
            id=self.id,
            session_id=SessionId(self.session_id),
            phase=self.phase,
            from_status=SessionStatus(self.from_status) if self.from_status else None,
            to_status=SessionStatus(self.to_status) if self.to_status else None,
            result=SchedulingResult(self.result),
            error_code=self.error_code,
            message=self.message,
            sub_steps=self.sub_steps,  # PydanticListColumn handles conversion
            attempts=self.attempts,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class KernelSchedulingHistoryRow(Base):
    __tablename__ = "kernel_scheduling_history"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    kernel_id: Mapped[uuid.UUID] = mapped_column("kernel_id", GUID, nullable=False, index=True)
    session_id: Mapped[uuid.UUID] = mapped_column("session_id", GUID, nullable=False, index=True)

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

    def to_data(self) -> KernelSchedulingHistoryData:
        return KernelSchedulingHistoryData(
            id=self.id,
            kernel_id=KernelId(self.kernel_id),
            session_id=SessionId(self.session_id),
            phase=self.phase,
            from_status=KernelSchedulingPhase(self.from_status) if self.from_status else None,
            to_status=KernelSchedulingPhase(self.to_status) if self.to_status else None,
            result=SchedulingResult(self.result),
            error_code=self.error_code,
            message=self.message,
            attempts=self.attempts,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class DeploymentHistoryRow(Base):
    __tablename__ = "deployment_history"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    deployment_id: Mapped[uuid.UUID] = mapped_column(
        "deployment_id", GUID, nullable=False, index=True
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

    def should_merge_with(self, new_row: DeploymentHistoryRow) -> bool:
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

    def to_data(self) -> DeploymentHistoryData:
        return DeploymentHistoryData(
            id=self.id,
            deployment_id=self.deployment_id,
            phase=self.phase,
            from_status=ModelDeploymentStatus(self.from_status) if self.from_status else None,
            to_status=ModelDeploymentStatus(self.to_status) if self.to_status else None,
            result=SchedulingResult(self.result),
            error_code=self.error_code,
            message=self.message,
            sub_steps=self.sub_steps,
            attempts=self.attempts,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class RouteHistoryRow(Base):
    __tablename__ = "route_history"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    route_id: Mapped[uuid.UUID] = mapped_column("route_id", GUID, nullable=False, index=True)
    deployment_id: Mapped[uuid.UUID] = mapped_column(
        "deployment_id", GUID, nullable=False, index=True
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

    def should_merge_with(self, new_row: RouteHistoryRow) -> bool:
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

    def to_data(self) -> RouteHistoryData:
        return RouteHistoryData(
            id=self.id,
            route_id=self.route_id,
            deployment_id=self.deployment_id,
            phase=self.phase,
            from_status=RouteStatus(self.from_status) if self.from_status else None,
            to_status=RouteStatus(self.to_status) if self.to_status else None,
            result=SchedulingResult(self.result),
            error_code=self.error_code,
            message=self.message,
            sub_steps=self.sub_steps,
            attempts=self.attempts,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
