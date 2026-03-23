"""
Common types for notification DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.common import OrderDirection

__all__ = (
    "EmailMessageInfo",
    "EmailSpecInfo",
    "NotificationChannelOrderField",
    "NotificationChannelSpecInfo",
    "NotificationChannelTypeDTO",
    "NotificationRuleOrderField",
    "NotificationRuleTypeDTO",
    "OrderDirection",
    "SMTPAuthInfo",
    "SMTPConnectionInfo",
    "WebhookSpecInfo",
)


class NotificationChannelTypeDTO(StrEnum):
    """Notification channel type enum for DTO layer."""

    WEBHOOK = "webhook"
    EMAIL = "email"


class NotificationRuleTypeDTO(StrEnum):
    """Notification rule type enum for DTO layer."""

    SESSION_STARTED = "session.started"
    SESSION_TERMINATED = "session.terminated"
    ARTIFACT_DOWNLOAD_COMPLETED = "artifact.download.completed"
    ENDPOINT_LIFECYCLE_CHANGED = "endpoint.lifecycle.changed"


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


class NotificationChannelSpecInfo(BaseResponseModel):
    """Base class for notification channel spec sub-types.

    Subclassed by WebhookSpecInfo and EmailSpecInfo so that Strawberry's
    pydantic interface dispatch can resolve the concrete GQL type from the
    concrete DTO type via NotificationChannelSpecGQL.from_pydantic().
    """

    channel_type: NotificationChannelTypeDTO = Field(description="Channel type discriminator")


class WebhookSpecInfo(NotificationChannelSpecInfo):
    """Webhook specification — matches WebhookSpecGQL structure."""

    url: str = Field(description="Webhook endpoint URL")


class SMTPConnectionInfo(BaseResponseModel):
    """SMTP connection settings — matches SMTPConnectionGQL structure."""

    host: str = Field(description="SMTP server host")
    port: int = Field(description="SMTP server port")
    use_tls: bool = Field(description="Whether TLS is enabled for SMTP connection")
    timeout: int = Field(description="SMTP connection timeout in seconds")


class EmailMessageInfo(BaseResponseModel):
    """Email message settings — matches EmailMessageGQL structure."""

    from_email: str = Field(description="Sender email address")
    to_emails: list[str] = Field(description="List of recipient email addresses")
    subject_template: str | None = Field(default=None, description="Email subject Jinja2 template")


class SMTPAuthInfo(BaseResponseModel):
    """SMTP authentication credentials — matches SMTPAuthGQL structure."""

    username: str | None = Field(description="SMTP auth username (password is never exposed)")


class EmailSpecInfo(NotificationChannelSpecInfo):
    """Email specification — matches EmailSpecGQL nested structure."""

    smtp: SMTPConnectionInfo = Field(description="SMTP connection settings")
    message: EmailMessageInfo = Field(description="Email message settings")
    auth: SMTPAuthInfo | None = Field(default=None, description="SMTP authentication credentials")
