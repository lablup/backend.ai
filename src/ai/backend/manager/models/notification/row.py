from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.notification import NotificationChannelID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.models.base import (
    GUID,
    Base,
)

__all__ = (
    "NotificationChannelRow",
    "NotificationRuleRow",
)


# ========== ORM Models ==========


class NotificationChannelRow(Base):
    __tablename__ = "notification_channels"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v7()")
    )
    name: Mapped[str] = mapped_column("name", sa.String(length=256), nullable=False)
    description: Mapped[str | None] = mapped_column("description", sa.Text, nullable=True)
    channel_type: Mapped[str] = mapped_column(
        "channel_type",
        sa.String(length=64),
        nullable=False,
    )
    config: Mapped[dict[str, Any]] = mapped_column(
        "config",
        sa.JSON(none_as_null=True),
        nullable=False,
    )
    enabled: Mapped[bool] = mapped_column(
        "enabled", sa.Boolean, nullable=False, default=True, index=True
    )
    created_by: Mapped[UserID] = mapped_column("created_by", GUID(UserID), nullable=False)
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


class NotificationRuleRow(Base):
    __tablename__ = "notification_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v7()")
    )
    name: Mapped[str] = mapped_column("name", sa.String(length=256), nullable=False)
    description: Mapped[str | None] = mapped_column("description", sa.Text, nullable=True)
    rule_type: Mapped[str] = mapped_column(
        "rule_type", sa.String(length=256), nullable=False, index=True
    )
    channel_id: Mapped[NotificationChannelID] = mapped_column(
        "channel_id", GUID(NotificationChannelID), nullable=False
    )
    message_template: Mapped[str] = mapped_column("message_template", sa.Text, nullable=False)
    enabled: Mapped[bool] = mapped_column(
        "enabled", sa.Boolean, nullable=False, default=True, index=True
    )
    created_by: Mapped[UserID] = mapped_column("created_by", GUID(UserID), nullable=False)
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
