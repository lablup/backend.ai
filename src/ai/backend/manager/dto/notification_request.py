import uuid
from typing import Optional

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.notification import (
    CreateNotificationChannelRequest,
    CreateNotificationRuleRequest,
    NotificationChannelFilter,
    NotificationChannelOrder,
    NotificationRuleFilter,
    NotificationRuleOrder,
    UpdateNotificationChannelRequest,
    UpdateNotificationRuleRequest,
)
from ai.backend.manager.data.notification import (
    NotificationChannelModifier,
    NotificationRuleModifier,
)
from ai.backend.manager.types import OptionalState


# Re-export common DTOs with BaseRequestModel for manager API
class CreateNotificationChannelReq(CreateNotificationChannelRequest, BaseRequestModel):
    """Manager API request to create a notification channel."""

    pass


class CreateNotificationRuleReq(CreateNotificationRuleRequest, BaseRequestModel):
    """Manager API request to create a notification rule."""

    pass


class UpdateNotificationChannelPathParam(BaseRequestModel):
    channel_id: uuid.UUID = Field(description="The notification channel ID to update")


class UpdateNotificationChannelBodyParam(UpdateNotificationChannelRequest, BaseRequestModel):
    """Manager API request to update a notification channel."""

    def to_modifier(self) -> NotificationChannelModifier:
        from ai.backend.common.data.notification import WebhookConfig

        modifier = NotificationChannelModifier()
        if self.name is not None:
            modifier.name = OptionalState.update(self.name)
        if self.description is not None:
            modifier.description = OptionalState.update(self.description)
        if self.config is not None:
            # config validator ensures this is WebhookConfig
            assert isinstance(self.config, WebhookConfig)
            modifier.config = OptionalState.update(self.config)
        if self.enabled is not None:
            modifier.enabled = OptionalState.update(self.enabled)
        return modifier


class GetNotificationChannelPathParam(BaseRequestModel):
    channel_id: uuid.UUID = Field(description="The notification channel ID to retrieve")


class DeleteNotificationChannelPathParam(BaseRequestModel):
    channel_id: uuid.UUID = Field(description="The notification channel ID to delete")


class SearchNotificationChannelsReq(BaseRequestModel):
    """Request body for searching notification channels with filters, orders, and pagination."""

    filter: Optional[NotificationChannelFilter] = Field(
        default=None, description="Filter conditions"
    )
    order: Optional[NotificationChannelOrder] = Field(
        default=None, description="Order specification"
    )
    limit: Optional[int] = Field(default=None, ge=1, le=1000, description="Maximum items to return")
    offset: Optional[int] = Field(default=None, ge=0, description="Number of items to skip")


# Notification Rule Request DTOs


class UpdateNotificationRulePathParam(BaseRequestModel):
    rule_id: uuid.UUID = Field(description="The notification rule ID to update")


class UpdateNotificationRuleBodyParam(UpdateNotificationRuleRequest, BaseRequestModel):
    """Manager API request to update a notification rule."""

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


class SearchNotificationRulesReq(BaseRequestModel):
    """Request body for searching notification rules with filters, orders, and pagination."""

    filter: Optional[NotificationRuleFilter] = Field(default=None, description="Filter conditions")
    order: Optional[NotificationRuleOrder] = Field(default=None, description="Order specification")
    limit: Optional[int] = Field(default=None, ge=1, le=1000, description="Maximum items to return")
    offset: Optional[int] = Field(default=None, ge=0, description="Number of items to skip")
