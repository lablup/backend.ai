import uuid
from typing import Optional, Union

from pydantic import Field, field_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.manager.data.notification import (
    NotificationChannelModifier,
    NotificationChannelType,
    NotificationRuleModifier,
    NotificationRuleType,
    WebhookConfig,
)
from ai.backend.manager.types import OptionalState

# Type alias for channel configuration union (currently only webhook, can be extended)
NotificationChannelConfig = Union[WebhookConfig]


class CreateNotificationChannelReq(BaseRequestModel):
    name: str = Field(description="Channel name")
    description: Optional[str] = Field(default=None, description="Channel description")
    channel_type: NotificationChannelType = Field(description="Channel type (e.g., WEBHOOK)")
    config: NotificationChannelConfig = Field(description="Channel configuration")
    enabled: bool = Field(default=True, description="Whether the channel is enabled")

    @field_validator("config", mode="before")
    @classmethod
    def validate_config(
        cls, v: Union[dict, NotificationChannelConfig], info
    ) -> NotificationChannelConfig:
        """Validate and convert config based on channel_type."""
        if isinstance(v, WebhookConfig):
            return v
        # For dict input, convert to appropriate config type
        if isinstance(v, dict):
            channel_type = info.data.get("channel_type")
            match channel_type:
                case NotificationChannelType.WEBHOOK:
                    return WebhookConfig(**v)
                case _:
                    raise ValueError(f"Unsupported channel_type: {channel_type}")
        raise ValueError(f"Invalid config type: {type(v)}")


class UpdateNotificationChannelPathParam(BaseRequestModel):
    channel_id: uuid.UUID = Field(description="The notification channel ID to update")


class UpdateNotificationChannelBodyParam(BaseRequestModel):
    name: Optional[str] = Field(default=None, description="Updated channel name")
    description: Optional[str] = Field(default=None, description="Updated channel description")
    config: Optional[NotificationChannelConfig] = Field(
        default=None, description="Updated channel configuration"
    )
    enabled: Optional[bool] = Field(default=None, description="Updated enabled status")

    @field_validator("config", mode="before")
    @classmethod
    def validate_config(
        cls, v: Optional[Union[dict, NotificationChannelConfig]]
    ) -> Optional[NotificationChannelConfig]:
        """Validate and convert config if provided."""
        if v is None:
            return None
        if isinstance(v, WebhookConfig):
            return v
        if isinstance(v, dict):
            return WebhookConfig(**v)
        raise ValueError(f"Invalid config type: {type(v)}")

    def to_modifier(self) -> NotificationChannelModifier:
        modifier = NotificationChannelModifier()
        if self.name is not None:
            modifier.name = OptionalState.update(self.name)
        if self.description is not None:
            modifier.description = OptionalState.update(self.description)
        if self.config is not None:
            modifier.config = OptionalState.update(self.config)
        if self.enabled is not None:
            modifier.enabled = OptionalState.update(self.enabled)
        return modifier


class GetNotificationChannelPathParam(BaseRequestModel):
    channel_id: uuid.UUID = Field(description="The notification channel ID to retrieve")


class DeleteNotificationChannelPathParam(BaseRequestModel):
    channel_id: uuid.UUID = Field(description="The notification channel ID to delete")


class ListNotificationChannelsReq(BaseRequestModel):
    enabled_only: bool = Field(default=False, description="Only list enabled channels")


# Notification Rule Request DTOs


class CreateNotificationRuleReq(BaseRequestModel):
    name: str = Field(description="Rule name")
    description: Optional[str] = Field(default=None, description="Rule description")
    rule_type: NotificationRuleType = Field(
        description="Rule type (e.g., SESSION_STARTED, SESSION_TERMINATED)"
    )
    channel_id: uuid.UUID = Field(description="ID of the channel to use for notifications")
    message_template: str = Field(
        description="Jinja2 template for notification message (e.g., 'Session {{ session_id }} started')"
    )
    enabled: bool = Field(default=True, description="Whether the rule is enabled")


class UpdateNotificationRulePathParam(BaseRequestModel):
    rule_id: uuid.UUID = Field(description="The notification rule ID to update")


class UpdateNotificationRuleBodyParam(BaseRequestModel):
    name: Optional[str] = Field(default=None, description="Updated rule name")
    description: Optional[str] = Field(default=None, description="Updated rule description")
    message_template: Optional[str] = Field(default=None, description="Updated message template")
    enabled: Optional[bool] = Field(default=None, description="Updated enabled status")

    def to_modifier(self) -> NotificationRuleModifier:
        modifier = NotificationRuleModifier()
        if self.name is not None:
            modifier.name = OptionalState.update(self.name)
        if self.description is not None:
            modifier.description = OptionalState.update(self.description)
        if self.message_template is not None:
            modifier.message_template = OptionalState.update(self.message_template)
        if self.enabled is not None:
            modifier.enabled = OptionalState.update(self.enabled)
        return modifier


class GetNotificationRulePathParam(BaseRequestModel):
    rule_id: uuid.UUID = Field(description="The notification rule ID to retrieve")


class DeleteNotificationRulePathParam(BaseRequestModel):
    rule_id: uuid.UUID = Field(description="The notification rule ID to delete")


class ListNotificationRulesReq(BaseRequestModel):
    enabled_only: bool = Field(default=False, description="Only list enabled rules")
    rule_type: Optional[NotificationRuleType] = Field(
        default=None, description="Filter by rule type"
    )
