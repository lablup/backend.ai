import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.data.notification import (
    NotificationChannelType,
    NotificationRuleType,
    WebhookConfig,
)
from ai.backend.manager.data.notification import (
    NotificationChannelData,
    NotificationRuleData,
)

# Notification DTO Models (Pydantic models for external API)


class NotificationChannelDTO(BaseModel):
    """DTO for notification channel in API responses."""

    id: uuid.UUID = Field(description="Channel ID")
    name: str = Field(description="Channel name")
    description: Optional[str] = Field(default=None, description="Channel description")
    channel_type: NotificationChannelType = Field(description="Channel type")
    config: WebhookConfig = Field(description="Channel configuration")
    enabled: bool = Field(description="Whether the channel is enabled")
    created_by: uuid.UUID = Field(description="User ID who created this channel")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")

    @classmethod
    def from_data(cls, data: NotificationChannelData) -> "NotificationChannelDTO":
        """Convert NotificationChannelData to DTO."""
        return cls(
            id=data.id,
            name=data.name,
            description=data.description,
            channel_type=data.channel_type,
            config=data.config,
            enabled=data.enabled,
            created_by=data.created_by,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )


class NotificationRuleDTO(BaseModel):
    """DTO for notification rule in API responses."""

    id: uuid.UUID = Field(description="Rule ID")
    name: str = Field(description="Rule name")
    description: Optional[str] = Field(default=None, description="Rule description")
    rule_type: NotificationRuleType = Field(description="Rule type")
    channel: NotificationChannelDTO = Field(description="Associated channel")
    message_template: str = Field(description="Jinja2 message template")
    enabled: bool = Field(description="Whether the rule is enabled")
    created_by: uuid.UUID = Field(description="User ID who created this rule")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")

    @classmethod
    def from_data(cls, data: NotificationRuleData) -> "NotificationRuleDTO":
        """Convert NotificationRuleData to DTO."""
        return cls(
            id=data.id,
            name=data.name,
            description=data.description,
            rule_type=data.rule_type,
            channel=NotificationChannelDTO.from_data(data.channel),
            message_template=data.message_template,
            enabled=data.enabled,
            created_by=data.created_by,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )


# Notification Channel Response DTOs


class CreateNotificationChannelResponse(BaseResponseModel):
    channel: NotificationChannelDTO


class GetNotificationChannelResponse(BaseResponseModel):
    channel: NotificationChannelDTO


class UpdateNotificationChannelResponse(BaseResponseModel):
    channel: NotificationChannelDTO


class DeleteNotificationChannelResponse(BaseResponseModel):
    deleted: bool


class ListNotificationChannelsResponse(BaseResponseModel):
    channels: list[NotificationChannelDTO]


# Notification Rule Response DTOs


class CreateNotificationRuleResponse(BaseResponseModel):
    rule: NotificationRuleDTO


class GetNotificationRuleResponse(BaseResponseModel):
    rule: NotificationRuleDTO


class UpdateNotificationRuleResponse(BaseResponseModel):
    rule: NotificationRuleDTO


class DeleteNotificationRuleResponse(BaseResponseModel):
    deleted: bool


class ListNotificationRulesResponse(BaseResponseModel):
    rules: list[NotificationRuleDTO]
