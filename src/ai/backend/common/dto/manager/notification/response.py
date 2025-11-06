"""
Response DTOs for notification system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .types import NotificationChannelType, NotificationRuleType

__all__ = (
    "WebhookConfigResponse",
    "NotificationChannelResponse",
    "NotificationRuleResponse",
    "CreateNotificationChannelResponse",
    "UpdateNotificationChannelResponse",
    "DeleteNotificationChannelResponse",
    "GetNotificationChannelResponse",
    "ListNotificationChannelsResponse",
    "CreateNotificationRuleResponse",
    "UpdateNotificationRuleResponse",
    "DeleteNotificationRuleResponse",
    "GetNotificationRuleResponse",
    "ListNotificationRulesResponse",
    "PaginationInfo",
)


class WebhookConfigResponse(BaseModel):
    """Response model for webhook configuration."""

    url: str = Field(description="Webhook URL")


class NotificationChannelResponse(BaseModel):
    """Response model for notification channel."""

    id: UUID = Field(description="Channel ID")
    name: str = Field(description="Channel name")
    description: Optional[str] = Field(default=None, description="Channel description")
    channel_type: NotificationChannelType = Field(description="Channel type")
    config: WebhookConfigResponse = Field(description="Channel configuration")
    enabled: bool = Field(description="Whether the channel is enabled")
    created_at: datetime = Field(description="Creation timestamp")
    created_by: UUID = Field(description="ID of user who created the channel")


class NotificationRuleResponse(BaseModel):
    """Response model for notification rule."""

    id: UUID = Field(description="Rule ID")
    name: str = Field(description="Rule name")
    description: Optional[str] = Field(default=None, description="Rule description")
    rule_type: NotificationRuleType = Field(description="Rule type")
    channel: NotificationChannelResponse = Field(description="Associated channel")
    message_template: str = Field(description="Jinja2 template for notification message")
    enabled: bool = Field(description="Whether the rule is enabled")
    created_at: datetime = Field(description="Creation timestamp")
    created_by: UUID = Field(description="ID of user who created the rule")


class CreateNotificationChannelResponse(BaseModel):
    """Response for creating a notification channel."""

    channel: NotificationChannelResponse = Field(description="Created channel")


class UpdateNotificationChannelResponse(BaseModel):
    """Response for updating a notification channel."""

    channel: NotificationChannelResponse = Field(description="Updated channel")


class DeleteNotificationChannelResponse(BaseModel):
    """Response for deleting a notification channel."""

    id: UUID = Field(description="Deleted channel ID")


class GetNotificationChannelResponse(BaseModel):
    """Response for getting a notification channel."""

    channel: NotificationChannelResponse = Field(description="Channel data")


class PaginationInfo(BaseModel):
    """Pagination information."""

    total: int = Field(description="Total number of items")
    offset: int = Field(description="Number of items skipped")
    limit: Optional[int] = Field(default=None, description="Maximum items returned")


class ListNotificationChannelsResponse(BaseModel):
    """Response for listing notification channels."""

    channels: list[NotificationChannelResponse] = Field(description="List of channels")
    pagination: PaginationInfo = Field(description="Pagination information")


class CreateNotificationRuleResponse(BaseModel):
    """Response for creating a notification rule."""

    rule: NotificationRuleResponse = Field(description="Created rule")


class UpdateNotificationRuleResponse(BaseModel):
    """Response for updating a notification rule."""

    rule: NotificationRuleResponse = Field(description="Updated rule")


class DeleteNotificationRuleResponse(BaseModel):
    """Response for deleting a notification rule."""

    id: UUID = Field(description="Deleted rule ID")


class GetNotificationRuleResponse(BaseModel):
    """Response for getting a notification rule."""

    rule: NotificationRuleResponse = Field(description="Rule data")


class ListNotificationRulesResponse(BaseModel):
    """Response for listing notification rules."""

    rules: list[NotificationRuleResponse] = Field(description="List of rules")
    pagination: PaginationInfo = Field(description="Pagination information")
