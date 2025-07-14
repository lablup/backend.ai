from __future__ import annotations

import enum
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

import sqlalchemy as sa

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.actions.types import OperationStatus

from .base import (
    GUID,
    Base,
    IDColumn,
    StrEnumType,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("AuditLogRow",)


class AuditLogEntityType(enum.StrEnum):
    IMAGE = "image"
    CONTAINER_REGISTRY = "container_registry"
    DOMAIN = "domain"
    GROUP = "group"
    AGENT = "agent"
    KEYPAIR_RESOURCE_POLICY = "keypair_resource_policy"
    PROJECT_RESOURCE_POLICY = "project_resource_policy"
    USER_RESOURCE_POLICY = "user_resource_policy"
    RESOURCE_PRESET = "resource_preset"
    SESSION = "session"
    USER = "user"
    VFOLDER = "vfolder"
    VFOLDER_INVITATION = "vfolder_invitation"


class AuditLogRow(Base):
    __tablename__ = "audit_logs"

    id = IDColumn("id")

    entity_type = sa.Column("entity_type", sa.String, index=True, nullable=False)
    operation = sa.Column("operation", sa.String, index=True, nullable=False)

    entity_id = sa.Column(
        "entity_id",
        sa.String,
        nullable=True,
        index=True,
    )

    created_at = sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
        index=True,
    )

    action_id = sa.Column("action_id", GUID, nullable=False)
    request_id = sa.Column("request_id", sa.String, nullable=True)
    triggered_by = sa.Column("triggered_by", sa.String, nullable=True)
    description = sa.Column("description", sa.String, nullable=False)
    duration = sa.Column("duration", sa.Interval, nullable=True)

    status = sa.Column(
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
        entity_id: Optional[str | uuid.UUID] = None,
        request_id: Optional[str] = None,
        triggered_by: Optional[str] = None,
        duration: Optional[timedelta] = None,
    ):
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
