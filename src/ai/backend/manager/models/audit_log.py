from __future__ import annotations

import enum
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

import sqlalchemy as sa

from ai.backend.logging import BraceStyleAdapter

from .base import (
    GUID,
    Base,
    IDColumn,
    StrEnumType,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("AuditLogRow", "ImageAuditLogOperationType")


class AuditLogEntityType(enum.StrEnum):
    IMAGE = "image"


class ImageAuditLogOperationType(enum.StrEnum):
    SESSION_CREATE = "session_create"
    UPDATE = "update"  # Rescan and update image metadata
    PULL = "pull"  # Pull image from the registry


class OperationStatus(enum.StrEnum):
    SUCCESS = "success"
    ERROR = "error"


AuditLogOperationType = ImageAuditLogOperationType


class AuditLogRow(Base):
    __tablename__ = "audit_logs"

    id = IDColumn("id")

    entity_type = sa.Column("entity_type", sa.String, index=True, nullable=False)
    operation = sa.Column("operation", sa.String, index=True, nullable=False)

    entity_id = sa.Column(
        "entity_id",
        sa.String,
        nullable=False,
        index=True,
    )

    created_at = sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
        index=True,
    )

    request_id = sa.Column("request_id", GUID, nullable=False)
    description = sa.Column("description", sa.String, nullable=False)
    duration = sa.Column("duration", sa.Interval, nullable=False)

    status = sa.Column(
        "status",
        StrEnumType(OperationStatus),
        nullable=False,
    )

    def __init__(
        self,
        entity_type: AuditLogEntityType,
        operation: AuditLogOperationType,
        entity_id: str | uuid.UUID,
        request_id: uuid.UUID,
        description: str,
        duration: timedelta,
        created_at: Optional[datetime] = None,
        status: OperationStatus = OperationStatus.SUCCESS,
    ):
        self.entity_type = entity_type.value
        self.operation = operation.value
        self.entity_id = str(entity_id) if isinstance(entity_id, uuid.UUID) else entity_id
        self.request_id = request_id
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
            f"request_id: {self.request_id}, "
            f"description: {self.description}, "
            f"duration: {self.duration}, "
            f"status: {self.status.value}"
            f")"
        )

    def __repr__(self) -> str:
        return self.__str__()
