"""
Request DTOs for notification DTO v2.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel
from ai.backend.common.data.notification.types import (
    EmailSpec,
    NotificationChannelType,
    NotificationRuleType,
    WebhookSpec,
)

__all__ = (
    "CreateNotificationChannelInput",
    "CreateNotificationRuleInput",
    "DeleteNotificationChannelInput",
    "DeleteNotificationRuleInput",
    "UpdateNotificationChannelInput",
    "UpdateNotificationRuleInput",
    "ValidateNotificationChannelInput",
    "ValidateNotificationRuleInput",
)


class CreateNotificationChannelInput(BaseRequestModel):
    """Input for creating a notification channel."""

    name: str = Field(min_length=1, max_length=256, description="Channel name")
    description: str | None = Field(default=None, description="Channel description")
    channel_type: NotificationChannelType = Field(description="Channel type")
    spec: WebhookSpec | EmailSpec = Field(description="Channel specification")
    enabled: bool = Field(default=True, description="Whether the channel is enabled")

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("name must not be blank or whitespace-only")
        return stripped


class UpdateNotificationChannelInput(BaseRequestModel):
    """Input for updating a notification channel."""

    name: str | None = Field(default=None, description="Updated channel name")
    description: str | Sentinel | None = Field(
        default=SENTINEL,
        description="Updated channel description. Use SENTINEL to clear.",
    )
    spec: WebhookSpec | EmailSpec | None = Field(
        default=None, description="Updated channel specification"
    )
    enabled: bool | None = Field(default=None, description="Updated enabled status")

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str | None) -> str | None:
        if v is None:
            return v
        stripped = v.strip()
        if not stripped:
            raise ValueError("name must not be blank or whitespace-only")
        return stripped


class DeleteNotificationChannelInput(BaseRequestModel):
    """Input for deleting a notification channel."""

    id: UUID = Field(description="Channel ID to delete")


class CreateNotificationRuleInput(BaseRequestModel):
    """Input for creating a notification rule."""

    name: str = Field(min_length=1, max_length=256, description="Rule name")
    description: str | None = Field(default=None, description="Rule description")
    rule_type: NotificationRuleType = Field(description="Rule type")
    channel_id: UUID = Field(description="ID of the channel to use")
    message_template: str = Field(
        max_length=65536,
        description="Jinja2 template for notification message (max 64KB)",
    )
    enabled: bool = Field(default=True, description="Whether the rule is enabled")

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("name must not be blank or whitespace-only")
        return stripped


class UpdateNotificationRuleInput(BaseRequestModel):
    """Input for updating a notification rule."""

    name: str | None = Field(default=None, description="Updated rule name")
    description: str | Sentinel | None = Field(
        default=SENTINEL,
        description="Updated rule description. Use SENTINEL to clear.",
    )
    message_template: str | None = Field(
        default=None,
        max_length=65536,
        description="Updated message template (max 64KB)",
    )
    enabled: bool | None = Field(default=None, description="Updated enabled status")

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str | None) -> str | None:
        if v is None:
            return v
        stripped = v.strip()
        if not stripped:
            raise ValueError("name must not be blank or whitespace-only")
        return stripped


class DeleteNotificationRuleInput(BaseRequestModel):
    """Input for deleting a notification rule."""

    id: UUID = Field(description="Rule ID to delete")


class ValidateNotificationChannelInput(BaseRequestModel):
    """Input for validating a notification channel by sending a test message."""

    id: UUID = Field(description="Channel ID to validate")
    test_message: str = Field(
        max_length=5000,
        description="Test message to send through the channel (max 5KB)",
    )


class ValidateNotificationRuleInput(BaseRequestModel):
    """Input for validating a notification rule by rendering its message template."""

    id: UUID = Field(description="Rule ID to validate")
    notification_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Test notification data to use in template rendering",
    )
