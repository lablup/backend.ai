"""
Response DTOs for notification DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

from .types import (
    EmailSpecInfo,
    NotificationChannelTypeDTO,
    NotificationRuleTypeDTO,
    WebhookSpecInfo,
)

__all__ = (
    "CreateNotificationChannelPayload",
    "CreateNotificationRulePayload",
    "DeleteNotificationChannelPayload",
    "DeleteNotificationRulePayload",
    "GetNotificationChannelPayload",
    "GetNotificationRulePayload",
    "NotificationChannelNode",
    "NotificationRuleNode",
    "SearchNotificationChannelsPayload",
    "SearchNotificationRulesPayload",
    "UpdateNotificationChannelPayload",
    "UpdateNotificationRulePayload",
    "ValidateNotificationChannelPayload",
    "ValidateNotificationRulePayload",
)


class NotificationChannelNode(BaseResponseModel):
    """Node model representing a notification channel entity."""

    id: UUID = Field(description="Channel ID")
    name: str = Field(description="Channel name")
    description: str | None = Field(default=None, description="Channel description")
    channel_type: NotificationChannelTypeDTO = Field(description="Channel type")
    spec: WebhookSpecInfo | EmailSpecInfo = Field(description="Channel specification")
    enabled: bool = Field(description="Whether the channel is enabled")
    created_at: datetime = Field(description="Creation timestamp")
    created_by: UUID = Field(description="ID of user who created the channel")
    updated_at: datetime = Field(description="Last update timestamp")


class NotificationRuleNode(BaseResponseModel):
    """Node model representing a notification rule entity."""

    id: UUID = Field(description="Rule ID")
    name: str = Field(description="Rule name")
    description: str | None = Field(default=None, description="Rule description")
    rule_type: NotificationRuleTypeDTO = Field(description="Rule type")
    channel: NotificationChannelNode = Field(description="Associated notification channel")
    message_template: str = Field(description="Jinja2 template for notification message")
    enabled: bool = Field(description="Whether the rule is enabled")
    created_at: datetime = Field(description="Creation timestamp")
    created_by: UUID = Field(description="ID of user who created the rule")
    updated_at: datetime = Field(description="Last update timestamp")


class GetNotificationChannelPayload(BaseResponseModel):
    """Payload for notification channel get result."""

    item: NotificationChannelNode = Field(description="Retrieved notification channel")


class GetNotificationRulePayload(BaseResponseModel):
    """Payload for notification rule get result."""

    item: NotificationRuleNode = Field(description="Retrieved notification rule")


class CreateNotificationChannelPayload(BaseResponseModel):
    """Payload for notification channel creation mutation result."""

    channel: NotificationChannelNode = Field(description="Created notification channel")


class UpdateNotificationChannelPayload(BaseResponseModel):
    """Payload for notification channel update mutation result."""

    channel: NotificationChannelNode = Field(description="Updated notification channel")


class DeleteNotificationChannelPayload(BaseResponseModel):
    """Payload for notification channel deletion mutation result."""

    id: UUID = Field(description="ID of the deleted notification channel")


class CreateNotificationRulePayload(BaseResponseModel):
    """Payload for notification rule creation mutation result."""

    rule: NotificationRuleNode = Field(description="Created notification rule")


class UpdateNotificationRulePayload(BaseResponseModel):
    """Payload for notification rule update mutation result."""

    rule: NotificationRuleNode = Field(description="Updated notification rule")


class DeleteNotificationRulePayload(BaseResponseModel):
    """Payload for notification rule deletion mutation result."""

    id: UUID = Field(description="ID of the deleted notification rule")


class ValidateNotificationChannelPayload(BaseResponseModel):
    """Payload for notification channel validation result."""

    id: UUID = Field(description="ID of the validated notification channel")


class ValidateNotificationRulePayload(BaseResponseModel):
    """Payload for notification rule validation result."""

    message: str = Field(description="The rendered message from the template")


class SearchNotificationChannelsPayload(BaseResponseModel):
    """Payload for notification channel search result."""

    items: list[NotificationChannelNode] = Field(description="List of matching channels")
    total_count: int = Field(description="Total number of matching channels")
    has_next_page: bool = Field(description="Whether there is a next page")
    has_previous_page: bool = Field(description="Whether there is a previous page")


class SearchNotificationRulesPayload(BaseResponseModel):
    """Payload for notification rule search result."""

    items: list[NotificationRuleNode] = Field(description="List of matching rules")
    total_count: int = Field(description="Total number of matching rules")
    has_next_page: bool = Field(description="Whether there is a next page")
    has_previous_page: bool = Field(description="Whether there is a previous page")
