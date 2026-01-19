from __future__ import annotations

from pydantic import BaseModel, Field

from ai.backend.common.types import CIStrEnum


class NotificationChannelType(CIStrEnum):
    """Notification channel types."""

    WEBHOOK = "webhook"
    EMAIL = "email"


class NotificationRuleType(CIStrEnum):
    """Types of notification rules that can be created."""

    SESSION_STARTED = "session.started"
    SESSION_TERMINATED = "session.terminated"
    ARTIFACT_DOWNLOAD_COMPLETED = "artifact.download.completed"


class WebhookSpec(BaseModel):
    """Configuration for webhook notification channel."""

    url: str = Field(description="Webhook endpoint URL")
    method: str = Field(default="POST", description="HTTP method (POST or GET)")
    content_type: str = Field(
        default="application/json", description="Content-Type header for the request body"
    )
    headers: dict[str, str] = Field(
        default_factory=dict, description="Additional HTTP headers to send"
    )
    timeout: int = Field(default=30, description="Request timeout in seconds")
    success_status_codes: list[int] = Field(
        default=[200, 201, 202, 204],
        description="HTTP status codes considered as successful delivery",
    )


class SMTPAuth(BaseModel):
    """SMTP authentication credentials."""

    username: str | None = Field(default=None, description="SMTP username for authentication")
    password: str | None = Field(
        default=None,
        description="SMTP password for authentication",
    )


class SMTPConnection(BaseModel):
    """SMTP server connection settings."""

    host: str = Field(description="SMTP server host")
    port: int = Field(ge=1, le=65535, description="SMTP server port")
    use_tls: bool = Field(default=True, description="Whether to use STARTTLS for secure connection")
    timeout: int = Field(default=30, gt=0, description="SMTP connection timeout in seconds")


class EmailMessage(BaseModel):
    """Email message settings."""

    from_email: str = Field(description="Sender email address")
    to_emails: list[str] = Field(min_length=1, description="List of recipient email addresses")
    subject_template: str | None = Field(
        default=None,
        description="Template for the email subject. If None, the first line of the message will be used.",
    )


class EmailSpec(BaseModel):
    """Configuration for email notification channel."""

    smtp: SMTPConnection = Field(description="SMTP server connection settings")
    message: EmailMessage = Field(description="Email message settings")
    auth: SMTPAuth | None = Field(default=None, description="SMTP authentication credentials")
