"""
Request DTOs for notification system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.data.notification.types import (
    EmailSpec,
    NotificationChannelType,
    NotificationRuleType,
    WebhookSpec,
)
from ai.backend.common.dto.manager.query import StringFilter

from .types import (
    NotificationChannelOrderField,
    NotificationRuleOrderField,
    OrderDirection,
)

__all__ = (
    "CreateNotificationChannelRequest",
    "CreateNotificationRuleRequest",
    "ListNotificationChannelsRequest",
    "ListNotificationRulesRequest",
    "NotificationChannelFilter",
    "NotificationChannelOrder",
    "NotificationRuleFilter",
    "NotificationRuleOrder",
    "SearchNotificationChannelsRequest",
    "SearchNotificationRulesRequest",
    "StringFilter",
    "UpdateNotificationChannelRequest",
    "UpdateNotificationRuleRequest",
    "ValidateNotificationChannelRequest",
    "ValidateNotificationRuleRequest",
)


class CreateNotificationChannelRequest(BaseRequestModel):
    """Request to create a notification channel."""

    name: str = Field(description="Channel name")
    description: Optional[str] = Field(default=None, description="Channel description")
    channel_type: NotificationChannelType = Field(description="Channel type")
    spec: WebhookSpec | EmailSpec = Field(description="Channel specification")
    enabled: bool = Field(default=True, description="Whether the channel is enabled")


class UpdateNotificationChannelRequest(BaseRequestModel):
    """Request to update a notification channel."""

    name: Optional[str] = Field(default=None, description="Updated channel name")
    description: Optional[str] = Field(default=None, description="Updated channel description")
    spec: WebhookSpec | EmailSpec | None = Field(
        default=None, description="Updated channel specification"
    )
    enabled: Optional[bool] = Field(default=None, description="Updated enabled status")


class NotificationChannelFilter(BaseRequestModel):
    """Filter for notification channels."""

    name: Optional[StringFilter] = Field(default=None, description="Filter by name")
    channel_types: Optional[list[NotificationChannelType]] = Field(
        default=None, description="Filter by channel types"
    )
    enabled: Optional[bool] = Field(default=None, description="Filter by enabled status")


class NotificationChannelOrder(BaseRequestModel):
    """Order specification for notification channels."""

    field: NotificationChannelOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")


class ListNotificationChannelsRequest(BaseRequestModel):
    """Request to list notification channels."""

    filter: Optional[NotificationChannelFilter] = Field(default=None, description="Filter criteria")
    order: Optional[NotificationChannelOrder] = Field(default=None, description="Order by")
    limit: Optional[int] = Field(default=None, ge=1, le=1000, description="Maximum items")
    offset: Optional[int] = Field(default=None, ge=0, description="Number of items to skip")


class SearchNotificationChannelsRequest(BaseRequestModel):
    """Request body for searching notification channels with filters, orders, and pagination."""

    filter: Optional[NotificationChannelFilter] = Field(
        default=None, description="Filter conditions"
    )
    order: Optional[list[NotificationChannelOrder]] = Field(
        default=None, description="Order specifications"
    )
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class CreateNotificationRuleRequest(BaseRequestModel):
    """Request to create a notification rule."""

    name: str = Field(description="Rule name")
    description: Optional[str] = Field(default=None, description="Rule description")
    rule_type: NotificationRuleType = Field(description="Rule type")
    channel_id: UUID = Field(description="ID of the channel to use")
    message_template: str = Field(
        max_length=65536, description="Jinja2 template for notification message (max 64KB)"
    )
    enabled: bool = Field(default=True, description="Whether the rule is enabled")


class UpdateNotificationRuleRequest(BaseRequestModel):
    """Request to update a notification rule."""

    name: Optional[str] = Field(default=None, description="Updated rule name")
    description: Optional[str] = Field(default=None, description="Updated rule description")
    message_template: Optional[str] = Field(
        default=None, max_length=65536, description="Updated message template (max 64KB)"
    )
    enabled: Optional[bool] = Field(default=None, description="Updated enabled status")


class NotificationRuleFilter(BaseRequestModel):
    """Filter for notification rules."""

    name: Optional[StringFilter] = Field(default=None, description="Filter by name")
    rule_types: Optional[list[NotificationRuleType]] = Field(
        default=None, description="Filter by rule types"
    )
    enabled: Optional[bool] = Field(default=None, description="Filter by enabled status")


class NotificationRuleOrder(BaseRequestModel):
    """Order specification for notification rules."""

    field: NotificationRuleOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")


class ListNotificationRulesRequest(BaseRequestModel):
    """Request to list notification rules."""

    filter: Optional[NotificationRuleFilter] = Field(default=None, description="Filter criteria")
    order: Optional[NotificationRuleOrder] = Field(default=None, description="Order by")
    limit: Optional[int] = Field(default=None, ge=1, le=1000, description="Maximum items")
    offset: Optional[int] = Field(default=None, ge=0, description="Number of items to skip")


class SearchNotificationRulesRequest(BaseRequestModel):
    """Request body for searching notification rules with filters, orders, and pagination."""

    filter: Optional[NotificationRuleFilter] = Field(default=None, description="Filter conditions")
    order: Optional[list[NotificationRuleOrder]] = Field(
        default=None, description="Order specifications"
    )
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class ValidateNotificationChannelRequest(BaseRequestModel):
    """Request body for validating a notification channel."""

    test_message: str = Field(
        max_length=5000,
        description="Test message to send through the channel (max 5KB)",
    )


class ValidateNotificationRuleRequest(BaseRequestModel):
    """Request body for validating a notification rule."""

    notification_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Test notification data to use in template rendering",
    )
