"""
Common types for notification DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.data.notification.types import (
    NotificationChannelType,
    NotificationRuleType,
)

__all__ = (
    "EmailSpecInfo",
    "NotificationChannelOrderField",
    "NotificationChannelType",
    "NotificationRuleOrderField",
    "NotificationRuleType",
    "OrderDirection",
    "WebhookSpecInfo",
)


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class NotificationChannelOrderField(StrEnum):
    """Fields available for ordering notification channels."""

    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class NotificationRuleOrderField(StrEnum):
    """Fields available for ordering notification rules."""

    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class WebhookSpecInfo(BaseResponseModel):
    """Compact webhook specification view for embedding in NotificationChannelNode."""

    url: str = Field(description="Webhook endpoint URL")


class EmailSpecInfo(BaseResponseModel):
    """Email specification view for embedding in NotificationChannelNode."""

    smtp_host: str = Field(description="SMTP server host")
    smtp_port: int = Field(description="SMTP server port")
    smtp_use_tls: bool = Field(description="Whether TLS is enabled for SMTP connection")
    smtp_timeout: int = Field(description="SMTP connection timeout in seconds")
    from_email: str = Field(description="Sender email address")
    to_emails: list[str] = Field(description="List of recipient email addresses")
    subject_template: str | None = Field(default=None, description="Email subject Jinja2 template")
    auth_username: str | None = Field(
        default=None, description="SMTP auth username (password is never exposed)"
    )
