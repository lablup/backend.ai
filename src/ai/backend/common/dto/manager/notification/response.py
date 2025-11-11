"""
Response DTOs for notification system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel

from .types import NotificationChannelType, NotificationRuleType

__all__ = (
    "WebhookConfigResponse",
    "NotificationChannelDTO",
    "NotificationRuleDTO",
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
    "ListNotificationRuleTypesResponse",
    "NotificationRuleTypeSchemaResponse",
    "ValidateNotificationChannelResponse",
    "ValidateNotificationRuleResponse",
    "PaginationInfo",
)


class WebhookConfigResponse(BaseResponseModel):
    """Response model for webhook configuration."""

    url: str = Field(description="Webhook URL")


class NotificationChannelDTO(BaseModel):
    """DTO for notification channel data."""

    id: UUID = Field(description="Channel ID")
    name: str = Field(description="Channel name")
    description: Optional[str] = Field(default=None, description="Channel description")
    channel_type: NotificationChannelType = Field(description="Channel type")
    config: WebhookConfigResponse = Field(description="Channel configuration")
    enabled: bool = Field(description="Whether the channel is enabled")
    created_at: datetime = Field(description="Creation timestamp")
    created_by: UUID = Field(description="ID of user who created the channel")
    updated_at: datetime = Field(description="Last update timestamp")


class NotificationRuleDTO(BaseModel):
    """DTO for notification rule data."""

    id: UUID = Field(description="Rule ID")
    name: str = Field(description="Rule name")
    description: Optional[str] = Field(default=None, description="Rule description")
    rule_type: NotificationRuleType = Field(description="Rule type")
    channel: NotificationChannelDTO = Field(description="Associated channel")
    message_template: str = Field(description="Jinja2 template for notification message")
    enabled: bool = Field(description="Whether the rule is enabled")
    created_at: datetime = Field(description="Creation timestamp")
    created_by: UUID = Field(description="ID of user who created the rule")
    updated_at: datetime = Field(description="Last update timestamp")


class CreateNotificationChannelResponse(BaseResponseModel):
    """Response for creating a notification channel."""

    channel: NotificationChannelDTO = Field(description="Created channel")


class UpdateNotificationChannelResponse(BaseResponseModel):
    """Response for updating a notification channel."""

    channel: NotificationChannelDTO = Field(description="Updated channel")


class DeleteNotificationChannelResponse(BaseResponseModel):
    """Response for deleting a notification channel."""

    deleted: bool = Field(description="Whether the channel was deleted")


class GetNotificationChannelResponse(BaseResponseModel):
    """Response for getting a notification channel."""

    channel: NotificationChannelDTO = Field(description="Channel data")


class PaginationInfo(BaseModel):
    """Pagination information."""

    total: int = Field(description="Total number of items")
    offset: int = Field(description="Number of items skipped")
    limit: Optional[int] = Field(default=None, description="Maximum items returned")


class ListNotificationChannelsResponse(BaseResponseModel):
    """Response for listing notification channels."""

    channels: list[NotificationChannelDTO] = Field(description="List of channels")
    pagination: PaginationInfo = Field(description="Pagination information")


class CreateNotificationRuleResponse(BaseResponseModel):
    """Response for creating a notification rule."""

    rule: NotificationRuleDTO = Field(description="Created rule")


class UpdateNotificationRuleResponse(BaseResponseModel):
    """Response for updating a notification rule."""

    rule: NotificationRuleDTO = Field(description="Updated rule")


class DeleteNotificationRuleResponse(BaseResponseModel):
    """Response for deleting a notification rule."""

    deleted: bool = Field(description="Whether the rule was deleted")


class GetNotificationRuleResponse(BaseResponseModel):
    """Response for getting a notification rule."""

    rule: NotificationRuleDTO = Field(description="Rule data")


class ListNotificationRulesResponse(BaseResponseModel):
    """Response for listing notification rules."""

    rules: list[NotificationRuleDTO] = Field(description="List of rules")
    pagination: PaginationInfo = Field(description="Pagination information")


class ValidateNotificationChannelResponse(BaseResponseModel):
    """Response for validating a notification channel."""

    channel_id: UUID = Field(description="ID of the validated channel")


class ValidateNotificationRuleResponse(BaseResponseModel):
    """Response for validating a notification rule."""

    message: str = Field(description="The rendered message from the template")


class ListNotificationRuleTypesResponse(BaseResponseModel):
    """Response for listing available notification rule types."""

    rule_types: list[NotificationRuleType] = Field(
        description="List of available notification rule types"
    )


class NotificationRuleTypeSchemaResponse(BaseResponseModel):
    """Response for getting notification rule type schema."""

    rule_type: NotificationRuleType = Field(
        description="The notification rule type for which the schema is provided"
    )
    json_schema: dict[str, Any] = Field(
        description="JSON schema describing the required notification_data structure for this rule type"
    )
