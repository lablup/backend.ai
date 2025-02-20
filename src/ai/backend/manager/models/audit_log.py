from __future__ import annotations

import enum
import logging
import uuid

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from ai.backend.logging import BraceStyleAdapter

from .base import (
    Base,
    IDColumn,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("AuditLogRow", "ImageAuditLogOperationType")


class AuditLogEntityType(enum.StrEnum):
    IMAGE = "image"


class ImageAuditLogOperationType(enum.StrEnum):
    SESSION_CREATE = "session_create"
    UPDATE = "update"  # Rescan and update image metadata
    PULL = "pull"  # Pull image from the registry


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
        index=True,
    )

    def __init__(
        self,
        entity_type: AuditLogEntityType,
        operation: AuditLogOperationType,
        entity_id: str | uuid.UUID,
    ):
        self.entity_type = entity_type.value
        self.operation = operation.value
        self.entity_id = str(entity_id) if isinstance(entity_id, uuid.UUID) else entity_id

    def __str__(self) -> str:
        return (
            f"AuditLogRow("
            f"entity_type: {self.entity_type}, "
            f"operation: {self.operation}, "
            f"created_at: {self.created_at}, "
            f"entity_id: {self.entity_id}"
            f")"
        )

    def __repr__(self) -> str:
        return self.__str__()

    @classmethod
    async def report_image(
        cls,
        db_session: AsyncSession,
        entity_type: AuditLogEntityType,
        operation: ImageAuditLogOperationType,
        entity_id: str | uuid.UUID,
    ) -> None:
        db_session.add(cls(entity_type, operation, entity_id))
        await db_session.flush()
