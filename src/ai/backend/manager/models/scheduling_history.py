from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from ai.backend.common.data.model_deployment.types import ModelDeploymentStatus
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

from .base import GUID, Base, IDColumn

__all__ = (
    "SessionSchedulingHistoryRow",
    "KernelSchedulingHistoryRow",
    "DeploymentHistoryRow",
    "RouteHistoryRow",
)


class SessionSchedulingHistoryRow(Base):
    __tablename__ = "session_scheduling_history"

    id = IDColumn()
    session_id = sa.Column("session_id", GUID, nullable=False, index=True)

    from_status = sa.Column("from_status", sa.String(length=64), nullable=True)
    to_status = sa.Column("to_status", sa.String(length=64), nullable=True)

    result = sa.Column("result", sa.String(length=32), nullable=False)
    error_code = sa.Column("error_code", sa.String(length=128), nullable=True)
    message = sa.Column("message", sa.Text, nullable=False)

    sub_steps = sa.Column("sub_steps", JSONB, nullable=True)

    attempts = sa.Column("attempts", sa.Integer, nullable=False, default=1)
    created_at = sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        default=sa.func.now(),
    )
    updated_at = sa.Column(
        "updated_at",
        sa.DateTime(timezone=True),
        nullable=False,
        default=sa.func.now(),
        onupdate=sa.func.now(),
    )

    def to_data(self) -> SessionSchedulingHistoryData:
        sub_steps: list[SubStepResult] | None = None
        if self.sub_steps:
            sub_steps = [
                SubStepResult(
                    phase=s["phase"],
                    name=s["name"],
                    result=SchedulingResult(s["result"]),
                    error_code=s.get("error_code"),
                    message=s.get("message"),
                    executed_at=s["executed_at"],
                )
                for s in self.sub_steps
            ]
        return SessionSchedulingHistoryData(
            id=self.id,
            session_id=self.session_id,
            from_status=SessionStatus(self.from_status) if self.from_status else None,
            to_status=SessionStatus(self.to_status) if self.to_status else None,
            result=SchedulingResult(self.result),
            error_code=self.error_code,
            message=self.message,
            sub_steps=sub_steps,
            attempts=self.attempts,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class KernelSchedulingHistoryRow(Base):
    __tablename__ = "kernel_scheduling_history"

    id = IDColumn()
    kernel_id = sa.Column("kernel_id", GUID, nullable=False, index=True)
    session_id = sa.Column("session_id", GUID, nullable=False, index=True)

    from_phase = sa.Column("from_phase", sa.String(length=64), nullable=True)
    to_phase = sa.Column("to_phase", sa.String(length=64), nullable=True)

    result = sa.Column("result", sa.String(length=32), nullable=False)
    error_code = sa.Column("error_code", sa.String(length=128), nullable=True)
    message = sa.Column("message", sa.Text, nullable=False)

    attempts = sa.Column("attempts", sa.Integer, nullable=False, default=1)
    created_at = sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        default=sa.func.now(),
    )
    updated_at = sa.Column(
        "updated_at",
        sa.DateTime(timezone=True),
        nullable=False,
        default=sa.func.now(),
        onupdate=sa.func.now(),
    )

    def to_data(self) -> KernelSchedulingHistoryData:
        return KernelSchedulingHistoryData(
            id=self.id,
            kernel_id=self.kernel_id,
            session_id=self.session_id,
            from_phase=KernelSchedulingPhase(self.from_phase) if self.from_phase else None,
            to_phase=KernelSchedulingPhase(self.to_phase) if self.to_phase else None,
            result=SchedulingResult(self.result),
            error_code=self.error_code,
            message=self.message,
            attempts=self.attempts,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class DeploymentHistoryRow(Base):
    __tablename__ = "deployment_history"

    id = IDColumn()
    deployment_id = sa.Column("deployment_id", GUID, nullable=False, index=True)

    from_status = sa.Column("from_status", sa.String(length=64), nullable=True)
    to_status = sa.Column("to_status", sa.String(length=64), nullable=True)

    result = sa.Column("result", sa.String(length=32), nullable=False)
    error_code = sa.Column("error_code", sa.String(length=128), nullable=True)
    message = sa.Column("message", sa.Text, nullable=False)

    attempts = sa.Column("attempts", sa.Integer, nullable=False, default=1)
    created_at = sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        default=sa.func.now(),
    )
    updated_at = sa.Column(
        "updated_at",
        sa.DateTime(timezone=True),
        nullable=False,
        default=sa.func.now(),
        onupdate=sa.func.now(),
    )

    def to_data(self) -> DeploymentHistoryData:
        return DeploymentHistoryData(
            id=self.id,
            deployment_id=self.deployment_id,
            from_status=ModelDeploymentStatus(self.from_status) if self.from_status else None,
            to_status=ModelDeploymentStatus(self.to_status) if self.to_status else None,
            result=SchedulingResult(self.result),
            error_code=self.error_code,
            message=self.message,
            attempts=self.attempts,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class RouteHistoryRow(Base):
    __tablename__ = "route_history"

    id = IDColumn()
    route_id = sa.Column("route_id", GUID, nullable=False, index=True)
    deployment_id = sa.Column("deployment_id", GUID, nullable=False, index=True)

    from_status = sa.Column("from_status", sa.String(length=64), nullable=True)
    to_status = sa.Column("to_status", sa.String(length=64), nullable=True)

    result = sa.Column("result", sa.String(length=32), nullable=False)
    error_code = sa.Column("error_code", sa.String(length=128), nullable=True)
    message = sa.Column("message", sa.Text, nullable=False)

    attempts = sa.Column("attempts", sa.Integer, nullable=False, default=1)
    created_at = sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        default=sa.func.now(),
    )
    updated_at = sa.Column(
        "updated_at",
        sa.DateTime(timezone=True),
        nullable=False,
        default=sa.func.now(),
        onupdate=sa.func.now(),
    )

    def to_data(self) -> RouteHistoryData:
        return RouteHistoryData(
            id=self.id,
            route_id=self.route_id,
            deployment_id=self.deployment_id,
            from_status=RouteStatus(self.from_status) if self.from_status else None,
            to_status=RouteStatus(self.to_status) if self.to_status else None,
            result=SchedulingResult(self.result),
            error_code=self.error_code,
            message=self.message,
            attempts=self.attempts,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
