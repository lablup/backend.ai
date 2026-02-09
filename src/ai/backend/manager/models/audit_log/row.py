from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.actions.types import OperationStatus
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.models.base import (
    GUID,
    Base,
    StrEnumType,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("AuditLogRow",)


class AuditLogRow(Base):  # type: ignore[misc]
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )

    entity_type: Mapped[str] = mapped_column("entity_type", sa.String, index=True, nullable=False)
    operation: Mapped[str] = mapped_column("operation", sa.String, index=True, nullable=False)

    entity_id: Mapped[str | None] = mapped_column(
        "entity_id",
        sa.String,
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
        index=True,
    )

    action_id: Mapped[uuid.UUID] = mapped_column("action_id", GUID, nullable=False)
    request_id: Mapped[str | None] = mapped_column("request_id", sa.String, nullable=True)
    triggered_by: Mapped[str | None] = mapped_column("triggered_by", sa.String, nullable=True)
    description: Mapped[str] = mapped_column("description", sa.String, nullable=False)
    duration: Mapped[timedelta | None] = mapped_column("duration", sa.Interval, nullable=True)

    status: Mapped[OperationStatus] = mapped_column(
        "status",
        StrEnumType(OperationStatus),
        nullable=False,
    )

    def __init__(
        self,
        entity_type: str,
        operation: str,
        action_id: uuid.UUID,
        description: str,
        created_at: datetime,
        status: OperationStatus,
        entity_id: str | uuid.UUID | None = None,
        request_id: str | None = None,
        triggered_by: str | None = None,
        duration: timedelta | None = None,
    ) -> None:
        self.entity_type = entity_type
        self.operation = operation
        self.action_id = action_id
        self.entity_id = str(entity_id) if isinstance(entity_id, uuid.UUID) else entity_id
        self.request_id = request_id
        self.triggered_by = triggered_by
        self.description = description
        self.duration = duration
        self.status = status
        self.created_at = created_at

    def __str__(self) -> str:
        return (
            f"AuditLogRow("
            f"entity_type: {self.entity_type}, "
            f"operation: {self.operation}, "
            f"created_at: {self.created_at}, "
            f"entity_id: {self.entity_id}, "
            f"action_id: {self.action_id}, "
            f"request_id: {self.request_id}, "
            f"triggered_by: {self.triggered_by}, "
            f"description: {self.description}, "
            f"duration: {self.duration}, "
            f"status: {self.status.value}"
            f")"
        )

    def __repr__(self) -> str:
        return self.__str__()

    def to_dataclass(self) -> AuditLogData:
        return AuditLogData(
            id=self.id,
            action_id=self.action_id,
            entity_type=self.entity_type,
            operation=self.operation,
            created_at=self.created_at,
            description=self.description,
            status=self.status,
            entity_id=self.entity_id,
            request_id=self.request_id,
            triggered_by=self.triggered_by,
            duration=self.duration,
        )
