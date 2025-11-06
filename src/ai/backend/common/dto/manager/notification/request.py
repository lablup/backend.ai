"""
Request DTOs for notification system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from .types import (
    NotificationChannelOrderField,
    NotificationChannelType,
    NotificationRuleOrderField,
    NotificationRuleType,
    OrderDirection,
    WebhookConfig,
)

__all__ = (
    "CreateNotificationChannelRequest",
    "UpdateNotificationChannelRequest",
    "ListNotificationChannelsRequest",
    "CreateNotificationRuleRequest",
    "UpdateNotificationRuleRequest",
    "ListNotificationRulesRequest",
    "StringFilter",
    "NotificationChannelFilter",
    "NotificationRuleFilter",
    "NotificationChannelOrder",
    "NotificationRuleOrder",
)


class CreateNotificationChannelRequest(BaseModel):
    """Request to create a notification channel."""

    name: str = Field(description="Channel name")
    description: Optional[str] = Field(default=None, description="Channel description")
    channel_type: NotificationChannelType = Field(description="Channel type")
    config: dict[str, Any] | WebhookConfig = Field(description="Channel configuration")
    enabled: bool = Field(default=True, description="Whether the channel is enabled")

    @field_validator("config", mode="before")
    @classmethod
    def validate_config(cls, v: dict[str, Any] | WebhookConfig) -> WebhookConfig:
        """Convert dict to WebhookConfig if needed."""
        if isinstance(v, WebhookConfig):
            return v
        if isinstance(v, dict):
            return WebhookConfig(**v)
        raise ValueError(f"Invalid config type: {type(v)}")


class UpdateNotificationChannelRequest(BaseModel):
    """Request to update a notification channel."""

    name: Optional[str] = Field(default=None, description="Updated channel name")
    description: Optional[str] = Field(default=None, description="Updated channel description")
    config: Optional[dict[str, Any] | WebhookConfig] = Field(
        default=None, description="Updated channel configuration"
    )
    enabled: Optional[bool] = Field(default=None, description="Updated enabled status")

    @field_validator("config", mode="before")
    @classmethod
    def validate_config(
        cls, v: Optional[dict[str, Any] | WebhookConfig]
    ) -> Optional[WebhookConfig]:
        """Convert dict to WebhookConfig if needed."""
        if v is None:
            return None
        if isinstance(v, WebhookConfig):
            return v
        if isinstance(v, dict):
            return WebhookConfig(**v)
        raise ValueError(f"Invalid config type: {type(v)}")


class StringFilter(BaseModel):
    """String field filter with case-sensitive and case-insensitive options."""

    equals: Optional[str] = Field(default=None, description="Exact match (case-sensitive)")
    i_equals: Optional[str] = Field(default=None, description="Exact match (case-insensitive)")
    contains: Optional[str] = Field(default=None, description="Contains (case-sensitive)")
    i_contains: Optional[str] = Field(default=None, description="Contains (case-insensitive)")


class NotificationChannelFilter(BaseModel):
    """Filter for notification channels."""

    name: Optional[StringFilter] = Field(default=None, description="Filter by name")
    channel_types: Optional[list[NotificationChannelType]] = Field(
        default=None, description="Filter by channel types"
    )
    enabled: Optional[bool] = Field(default=None, description="Filter by enabled status")


class NotificationChannelOrder(BaseModel):
    """Order specification for notification channels."""

    field: NotificationChannelOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")


class ListNotificationChannelsRequest(BaseModel):
    """Request to list notification channels."""

    filter: Optional[NotificationChannelFilter] = Field(default=None, description="Filter criteria")
    order: Optional[NotificationChannelOrder] = Field(default=None, description="Order by")
    limit: Optional[int] = Field(default=None, ge=1, le=1000, description="Maximum items")
    offset: Optional[int] = Field(default=None, ge=0, description="Number of items to skip")


class CreateNotificationRuleRequest(BaseModel):
    """Request to create a notification rule."""

    name: str = Field(description="Rule name")
    description: Optional[str] = Field(default=None, description="Rule description")
    rule_type: NotificationRuleType = Field(description="Rule type")
    channel_id: UUID = Field(description="ID of the channel to use")
    message_template: str = Field(description="Jinja2 template for notification message")
    enabled: bool = Field(default=True, description="Whether the rule is enabled")


class UpdateNotificationRuleRequest(BaseModel):
    """Request to update a notification rule."""

    name: Optional[str] = Field(default=None, description="Updated rule name")
    description: Optional[str] = Field(default=None, description="Updated rule description")
    message_template: Optional[str] = Field(default=None, description="Updated message template")
    enabled: Optional[bool] = Field(default=None, description="Updated enabled status")


class NotificationRuleFilter(BaseModel):
    """Filter for notification rules."""

    name: Optional[StringFilter] = Field(default=None, description="Filter by name")
    rule_types: Optional[list[NotificationRuleType]] = Field(
        default=None, description="Filter by rule types"
    )
    enabled: Optional[bool] = Field(default=None, description="Filter by enabled status")


class NotificationRuleOrder(BaseModel):
    """Order specification for notification rules."""

    field: NotificationRuleOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")


class ListNotificationRulesRequest(BaseModel):
    """Request to list notification rules."""

    filter: Optional[NotificationRuleFilter] = Field(default=None, description="Filter criteria")
    order: Optional[NotificationRuleOrder] = Field(default=None, description="Order by")
    limit: Optional[int] = Field(default=None, ge=1, le=1000, description="Maximum items")
    offset: Optional[int] = Field(default=None, ge=0, description="Number of items to skip")
