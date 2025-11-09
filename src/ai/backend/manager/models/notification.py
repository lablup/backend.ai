from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from ..data.notification import (
    NotificationChannelData,
    NotificationChannelType,
    NotificationRuleData,
    NotificationRuleType,
    WebhookConfig,
)
from .base import (
    GUID,
    Base,
    IDColumn,
)

if TYPE_CHECKING:
    pass


__all__ = (
    "NotificationChannelType",
    "WebhookConfig",
    "NotificationChannelRow",
    "NotificationRuleRow",
)


# ========== ORM Models ==========


class NotificationChannelRow(Base):
    __tablename__ = "notification_channels"

    id = IDColumn()
    name = sa.Column("name", sa.String(length=256), nullable=False)
    description = sa.Column("description", sa.Text, nullable=True)
    channel_type = sa.Column(
        "channel_type",
        sa.String(length=64),
        nullable=False,
    )
    config = sa.Column(
        "config",
        sa.JSON(none_as_null=True),
        nullable=False,
    )
    enabled = sa.Column("enabled", sa.Boolean, nullable=False, default=True, index=True)
    created_by = sa.Column("created_by", GUID, nullable=False)
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

    # Relationships
    rules = relationship(
        "NotificationRuleRow",
        back_populates="channel",
        primaryjoin="NotificationChannelRow.id == foreign(NotificationRuleRow.channel_id)",
        foreign_keys=[id],
    )
    creator = relationship(
        "UserRow",
        primaryjoin="foreign(NotificationChannelRow.created_by) == UserRow.uuid",
        foreign_keys=[created_by],
        uselist=False,
    )

    def to_data(self) -> NotificationChannelData:
        """Convert Row to domain model data."""
        # Parse channel_type string to enum
        channel_type_enum = NotificationChannelType(self.channel_type)

        # Parse config based on channel_type
        match channel_type_enum:
            case NotificationChannelType.WEBHOOK:
                parsed_config = WebhookConfig(**self.config)
            case _:
                raise ValueError(f"Unknown channel type: {self.channel_type}")

        return NotificationChannelData(
            id=self.id,
            name=self.name,
            description=self.description,
            channel_type=channel_type_enum,
            config=parsed_config,
            enabled=self.enabled,
            created_by=self.created_by,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class NotificationRuleRow(Base):
    __tablename__ = "notification_rules"

    id = IDColumn()
    name = sa.Column("name", sa.String(length=256), nullable=False)
    description = sa.Column("description", sa.Text, nullable=True)
    rule_type = sa.Column("rule_type", sa.String(length=256), nullable=False, index=True)
    channel_id = sa.Column("channel_id", GUID, nullable=False)
    message_template = sa.Column("message_template", sa.Text, nullable=False)
    enabled = sa.Column("enabled", sa.Boolean, nullable=False, default=True, index=True)
    created_by = sa.Column("created_by", GUID, nullable=False)
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

    # Relationships
    channel = relationship(
        "NotificationChannelRow",
        back_populates="rules",
        primaryjoin="foreign(NotificationRuleRow.channel_id) == NotificationChannelRow.id",
        foreign_keys=[channel_id],
    )
    creator = relationship(
        "UserRow",
        primaryjoin="foreign(NotificationRuleRow.created_by) == UserRow.uuid",
        foreign_keys=[created_by],
        uselist=False,
    )

    def to_data(self) -> NotificationRuleData:
        """Convert Row to domain model data."""
        # Parse rule_type string to enum
        rule_type_enum = NotificationRuleType(self.rule_type)

        return NotificationRuleData(
            id=self.id,
            name=self.name,
            description=self.description,
            rule_type=rule_type_enum,
            channel=self.channel.to_data(),
            message_template=self.message_template,
            enabled=self.enabled,
            created_by=self.created_by,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
