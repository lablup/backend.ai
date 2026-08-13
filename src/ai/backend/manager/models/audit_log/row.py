from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from typing import override

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.identifier.action import ActionID
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.actions.types import ActionKind, OperationStatus
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.models.base import (
    GUID,
    Base,
    StrEnumType,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("AuditLogRow",)


class AuditLogRow(Base):
    """One audit record. ``action_kind`` says which shape wrote it; the target columns
    carry what that shape has. NULL ``action_kind`` means the row predates the column.
    """

    __tablename__ = "audit_logs"
    __table_args__ = (sa.Index("ix_audit_logs_lookup", "lookup_kind", "lookup_key"),)

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )

    action_kind: Mapped[ActionKind | None] = mapped_column(
        "action_kind", StrEnumType(ActionKind), nullable=True
    )

    entity_type: Mapped[str] = mapped_column("entity_type", sa.String, index=True, nullable=False)
    operation: Mapped[str] = mapped_column("operation", sa.String, index=True, nullable=False)

    # Declared by v2 actions; legacy rows carry the "entity_type:operation" spec type.
    action_name: Mapped[str] = mapped_column("action_name", sa.String, index=True, nullable=False)

    entity_id: Mapped[str | None] = mapped_column(
        "entity_id",
        sa.String,
        nullable=True,
        index=True,
    )

    # Plain indexed columns, not JSON: a lookup's key is the only thing identifying its
    # row, so it has to be filterable with the same string conditions as everything else.
    lookup_kind: Mapped[str | None] = mapped_column("lookup_kind", sa.String, nullable=True)
    lookup_key: Mapped[str | None] = mapped_column("lookup_key", sa.String, nullable=True)

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
    acted_as: Mapped[uuid.UUID | None] = mapped_column("acted_as", GUID, nullable=True)
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
        action_name: str,
        action_id: ActionID,
        description: str,
        created_at: datetime,
        status: OperationStatus,
        action_kind: ActionKind | None = None,
        entity_id: str | uuid.UUID | None = None,
        lookup_kind: str | None = None,
        lookup_key: str | None = None,
        request_id: str | None = None,
        triggered_by: str | None = None,
        acted_as: uuid.UUID | None = None,
        duration: timedelta | None = None,
    ) -> None:
        self.entity_type = entity_type
        self.operation = operation
        self.action_id = action_id
        self.action_kind = action_kind
        self.action_name = action_name
        self.entity_id = str(entity_id) if isinstance(entity_id, uuid.UUID) else entity_id
        self.lookup_kind = lookup_kind
        self.lookup_key = lookup_key
        self.request_id = request_id
        self.triggered_by = triggered_by
        self.acted_as = acted_as
        self.description = description
        self.duration = duration
        self.status = status
        self.created_at = created_at

    @override
    def __str__(self) -> str:
        return (
            f"AuditLogRow("
            f"entity_type: {self.entity_type}, "
            f"operation: {self.operation}, "
            f"created_at: {self.created_at}, "
            f"action_kind: {self.action_kind}, "
            f"action_name: {self.action_name}, "
            f"entity_id: {self.entity_id}, "
            f"lookup_kind: {self.lookup_kind}, "
            f"lookup_key: {self.lookup_key}, "
            f"action_id: {self.action_id}, "
            f"request_id: {self.request_id}, "
            f"triggered_by: {self.triggered_by}, "
            f"acted_as: {self.acted_as}, "
            f"description: {self.description}, "
            f"duration: {self.duration}, "
            f"status: {self.status.value}"
            f")"
        )

    @override
    def __repr__(self) -> str:
        return self.__str__()

    def to_dataclass(self) -> AuditLogData:
        return AuditLogData(
            id=self.id,
            action_id=self.action_id,
            action_kind=self.action_kind,
            action_name=self.action_name,
            entity_type=self.entity_type,
            operation=self.operation,
            created_at=self.created_at,
            description=self.description,
            status=self.status,
            entity_id=self.entity_id,
            lookup_kind=self.lookup_kind,
            lookup_key=self.lookup_key,
            request_id=self.request_id,
            triggered_by=self.triggered_by,
            acted_as=self.acted_as,
            duration=self.duration,
        )
