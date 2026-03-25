"""
Request DTOs for notification DTO v2.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel
from ai.backend.common.dto.manager.query import StringFilter

from .types import (
    NotificationChannelOrderField,
    NotificationChannelTypeDTO,
    NotificationRuleOrderField,
    NotificationRuleTypeDTO,
    OrderDirection,
)

__all__ = (
    "CreateNotificationChannelInput",
    "CreateNotificationRuleInput",
    "DeleteNotificationChannelInput",
    "DeleteNotificationRuleInput",
    "EmailMessageInputDTO",
    "EmailSpecInputDTO",
    "NotificationChannelFilter",
    "NotificationChannelOrder",
    "NotificationChannelSpecInputDTO",
    "NotificationChannelTypeFilter",
    "NotificationRuleFilter",
    "NotificationRuleOrder",
    "NotificationRuleTypeFilter",
    "SearchNotificationChannelsInput",
    "SearchNotificationRulesInput",
    "SMTPAuthInputDTO",
    "SMTPConnectionInputDTO",
    "UpdateNotificationChannelInput",
    "UpdateNotificationRuleInput",
    "ValidateNotificationChannelInput",
    "ValidateNotificationRuleInput",
    "WebhookSpecInputDTO",
)


class WebhookSpecInputDTO(BaseRequestModel):
    """Input for webhook channel specification."""

    url: str = Field(description="Webhook URL.")


class SMTPAuthInputDTO(BaseRequestModel):
    """Input for SMTP authentication credentials."""

    username: str | None = Field(default=None, description="SMTP username.")
    password: str | None = Field(default=None, description="SMTP password.")


class SMTPConnectionInputDTO(BaseRequestModel):
    """Input for SMTP server connection settings."""

    host: str = Field(description="SMTP host.")
    port: int = Field(description="SMTP port.")
    use_tls: bool = Field(default=True, description="Use TLS.")
    timeout: int = Field(default=30, description="Connection timeout in seconds.")


class EmailMessageInputDTO(BaseRequestModel):
    """Input for email message settings."""

    from_email: str = Field(description="Sender email address.")
    to_emails: list[str] = Field(description="Recipient email addresses.")
    subject_template: str | None = Field(default=None, description="Email subject template.")


class EmailSpecInputDTO(BaseRequestModel):
    """Input for email channel specification."""

    smtp: SMTPConnectionInputDTO = Field(description="SMTP connection settings.")
    message: EmailMessageInputDTO = Field(description="Email message settings.")
    auth: SMTPAuthInputDTO | None = Field(default=None, description="SMTP authentication.")


class NotificationChannelSpecInputDTO(BaseRequestModel):
    """Input for notification channel specification. Exactly one of webhook or email must be set."""

    webhook: WebhookSpecInputDTO | None = Field(default=None, description="Webhook specification.")
    email: EmailSpecInputDTO | None = Field(default=None, description="Email specification.")


class CreateNotificationChannelInput(BaseRequestModel):
    """Input for creating a notification channel."""

    name: str = Field(min_length=1, max_length=256, description="Channel name")
    description: str | None = Field(default=None, description="Channel description")
    channel_type: NotificationChannelTypeDTO = Field(description="Channel type")
    spec: NotificationChannelSpecInputDTO = Field(description="Channel specification")
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
    spec: NotificationChannelSpecInputDTO | None = Field(
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
    rule_type: NotificationRuleTypeDTO = Field(description="Rule type")
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
    notification_data: dict[str, Any] | None = Field(
        default=None,
        description="Test notification data to use in template rendering",
    )


# Search filter / order / input DTOs


class NotificationChannelTypeFilter(BaseRequestModel):
    """Filter for notification channel type field."""

    equals: NotificationChannelTypeDTO | None = Field(
        default=None, description="Matches channels with this exact type"
    )
    in_: list[NotificationChannelTypeDTO] | None = Field(
        default=None, description="Matches channels whose type is in this list"
    )
    not_equals: NotificationChannelTypeDTO | None = Field(
        default=None, description="Excludes channels with this exact type"
    )
    not_in: list[NotificationChannelTypeDTO] | None = Field(
        default=None, description="Excludes channels whose type is in this list"
    )


class NotificationChannelFilter(BaseRequestModel):
    """Filter for notification channel search queries."""

    name: StringFilter | None = Field(default=None, description="Filter by channel name")
    channel_type: NotificationChannelTypeFilter | None = Field(
        default=None, description="Filter by channel type"
    )
    enabled: bool | None = Field(default=None, description="Filter by enabled status")
    AND: list[NotificationChannelFilter] | None = Field(
        default=None, description="Combine with AND logic"
    )
    OR: list[NotificationChannelFilter] | None = Field(
        default=None, description="Combine with OR logic"
    )
    NOT: list[NotificationChannelFilter] | None = Field(default=None, description="Negate filters")


NotificationChannelFilter.model_rebuild()


class NotificationChannelOrder(BaseRequestModel):
    """Order specification for notification channel queries."""

    field: NotificationChannelOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.DESC, description="Order direction")


class SearchNotificationChannelsInput(BaseRequestModel):
    """Input for searching notification channels with filter, order, and pagination."""

    filter: NotificationChannelFilter | None = None
    order: list[NotificationChannelOrder] | None = None
    first: int | None = None
    after: str | None = None
    last: int | None = None
    before: str | None = None
    limit: int | None = None
    offset: int | None = None


class NotificationRuleTypeFilter(BaseRequestModel):
    """Filter for notification rule type field."""

    equals: NotificationRuleTypeDTO | None = Field(
        default=None, description="Matches rules with this exact type"
    )
    in_: list[NotificationRuleTypeDTO] | None = Field(
        default=None, description="Matches rules whose type is in this list"
    )
    not_equals: NotificationRuleTypeDTO | None = Field(
        default=None, description="Excludes rules with this exact type"
    )
    not_in: list[NotificationRuleTypeDTO] | None = Field(
        default=None, description="Excludes rules whose type is in this list"
    )


class NotificationRuleFilter(BaseRequestModel):
    """Filter for notification rule search queries."""

    name: StringFilter | None = Field(default=None, description="Filter by rule name")
    rule_type: NotificationRuleTypeFilter | None = Field(
        default=None, description="Filter by rule type"
    )
    enabled: bool | None = Field(default=None, description="Filter by enabled status")
    AND: list[NotificationRuleFilter] | None = Field(
        default=None, description="Combine with AND logic"
    )
    OR: list[NotificationRuleFilter] | None = Field(
        default=None, description="Combine with OR logic"
    )
    NOT: list[NotificationRuleFilter] | None = Field(default=None, description="Negate filters")


NotificationRuleFilter.model_rebuild()


class NotificationRuleOrder(BaseRequestModel):
    """Order specification for notification rule queries."""

    field: NotificationRuleOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.DESC, description="Order direction")


class SearchNotificationRulesInput(BaseRequestModel):
    """Input for searching notification rules with filter, order, and pagination."""

    filter: NotificationRuleFilter | None = None
    order: list[NotificationRuleOrder] | None = None
    first: int | None = None
    after: str | None = None
    last: int | None = None
    before: str | None = None
    limit: int | None = None
    offset: int | None = None
