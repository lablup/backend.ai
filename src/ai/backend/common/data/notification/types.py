from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class NotificationChannelType(StrEnum):
    """Notification channel types."""

    WEBHOOK = "webhook"


class NotificationRuleType(StrEnum):
    """Types of notification rules that can be created."""

    SESSION_STARTED = "session.started"
    SESSION_TERMINATED = "session.terminated"
    ARTIFACT_DOWNLOAD_COMPLETED = "artifact.download.completed"


class WebhookConfig(BaseModel):
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
