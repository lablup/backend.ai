"""GraphQL types, filters, and inputs for notification system."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Optional, Self, override

import strawberry
from strawberry import ID, UNSET
from strawberry.relay import Node, NodeID

from ai.backend.common.data.notification import (
    NotificationChannelType,
    NotificationRuleType,
    WebhookConfig,
)
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy
from ai.backend.manager.data.notification import (
    NotificationChannelData,
    NotificationRuleData,
)
from ai.backend.manager.models.notification import NotificationChannelRow, NotificationRuleRow
from ai.backend.manager.repositories.base import (
    Creator,
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.notification.creators import (
    NotificationChannelCreatorSpec,
    NotificationRuleCreatorSpec,
)
from ai.backend.manager.repositories.notification.options import (
    NotificationChannelConditions,
    NotificationChannelOrders,
    NotificationRuleConditions,
    NotificationRuleOrders,
)
from ai.backend.manager.repositories.notification.updaters import (
    NotificationChannelUpdaterSpec,
    NotificationRuleUpdaterSpec,
)
from ai.backend.manager.types import OptionalState

# GraphQL enum types


@strawberry.enum(name="NotificationChannelType", description="Notification channel types")
class NotificationChannelTypeGQL(StrEnum):
    WEBHOOK = "webhook"

    @classmethod
    def from_internal(cls, internal_type: NotificationChannelType) -> NotificationChannelTypeGQL:
        """Convert internal NotificationChannelType to GraphQL enum."""
        match internal_type:
            case NotificationChannelType.WEBHOOK:
                return cls.WEBHOOK

    def to_internal(self) -> NotificationChannelType:
        """Convert GraphQL enum to internal NotificationChannelType."""
        match self:
            case NotificationChannelTypeGQL.WEBHOOK:
                return NotificationChannelType.WEBHOOK


@strawberry.enum(name="NotificationRuleType", description="Notification rule types")
class NotificationRuleTypeGQL(StrEnum):
    SESSION_STARTED = "session.started"
    SESSION_TERMINATED = "session.terminated"
    ARTIFACT_DOWNLOAD_COMPLETED = "artifact.download.completed"

    @classmethod
    def from_internal(cls, internal_type: NotificationRuleType) -> NotificationRuleTypeGQL:
        """Convert internal NotificationRuleType to GraphQL enum."""
        match internal_type:
            case NotificationRuleType.SESSION_STARTED:
                return cls.SESSION_STARTED
            case NotificationRuleType.SESSION_TERMINATED:
                return cls.SESSION_TERMINATED
            case NotificationRuleType.ARTIFACT_DOWNLOAD_COMPLETED:
                return cls.ARTIFACT_DOWNLOAD_COMPLETED

    def to_internal(self) -> NotificationRuleType:
        """Convert GraphQL enum to internal NotificationRuleType."""
        match self:
            case NotificationRuleTypeGQL.SESSION_STARTED:
                return NotificationRuleType.SESSION_STARTED
            case NotificationRuleTypeGQL.SESSION_TERMINATED:
                return NotificationRuleType.SESSION_TERMINATED
            case NotificationRuleTypeGQL.ARTIFACT_DOWNLOAD_COMPLETED:
                return NotificationRuleType.ARTIFACT_DOWNLOAD_COMPLETED


# GraphQL object types


@strawberry.type
class WebhookConfigGQL:
    """GraphQL type for webhook configuration."""

    url: str

    @classmethod
    def from_dataclass(cls, config: WebhookConfig) -> Self:
        return cls(
            url=config.url,
        )


@strawberry.type(description="Notification channel")
class NotificationChannel(Node):
    id: NodeID[str]
    name: str
    description: Optional[str]
    channel_type: NotificationChannelTypeGQL
    config: WebhookConfigGQL
    enabled: bool
    created_at: datetime

    @classmethod
    def from_dataclass(cls, data: NotificationChannelData) -> Self:
        return cls(
            id=ID(str(data.id)),
            name=data.name,
            description=data.description,
            channel_type=NotificationChannelTypeGQL.from_internal(data.channel_type),
            config=WebhookConfigGQL.from_dataclass(data.config),
            enabled=data.enabled,
            created_at=data.created_at,
        )


@strawberry.type(description="Notification rule")
class NotificationRule(Node):
    id: NodeID[str]
    name: str
    description: Optional[str]
    rule_type: NotificationRuleTypeGQL
    channel: NotificationChannel
    message_template: str
    enabled: bool
    created_at: datetime

    @classmethod
    def from_dataclass(cls, data: NotificationRuleData) -> Self:
        return cls(
            id=ID(str(data.id)),
            name=data.name,
            description=data.description,
            rule_type=NotificationRuleTypeGQL.from_internal(data.rule_type),
            channel=NotificationChannel.from_dataclass(data.channel),
            message_template=data.message_template,
            enabled=data.enabled,
            created_at=data.created_at,
        )


# Filter and OrderBy types


@strawberry.enum
class NotificationChannelOrderField(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


@strawberry.input(description="Filter for notification channels")
class NotificationChannelFilter(GQLFilter):
    name: Optional[StringFilter] = None
    channel_type: Optional[list[NotificationChannelTypeGQL]] = None
    enabled: Optional[bool] = None

    AND: Optional[list[NotificationChannelFilter]] = None
    OR: Optional[list[NotificationChannelFilter]] = None
    NOT: Optional[list[NotificationChannelFilter]] = None

    @override
    def build_conditions(self) -> list[QueryCondition]:
        """Build query conditions from this filter.

        Returns a list containing a single combined QueryCondition that represents
        all filters with proper logical operators applied.
        """
        # Collect direct field conditions (these will be combined with AND)
        field_conditions: list[QueryCondition] = []

        # Apply name filter
        if self.name:
            name_condition = self.name.build_query_condition(
                contains_factory=NotificationChannelConditions.by_name_contains,
                equals_factory=NotificationChannelConditions.by_name_equals,
            )
            if name_condition:
                field_conditions.append(name_condition)

        # Apply channel_type filter
        if self.channel_type:
            internal_types = [ct.to_internal() for ct in self.channel_type]
            field_conditions.append(NotificationChannelConditions.by_channel_types(internal_types))

        # Apply enabled filter
        if self.enabled is not None:
            field_conditions.append(NotificationChannelConditions.by_enabled(self.enabled))

        # Handle AND logical operator - these are implicitly ANDed with field conditions
        if self.AND:
            for sub_filter in self.AND:
                field_conditions.extend(sub_filter.build_conditions())

        # Handle OR logical operator
        if self.OR:
            or_sub_conditions: list[QueryCondition] = []
            for sub_filter in self.OR:
                or_sub_conditions.extend(sub_filter.build_conditions())
            if or_sub_conditions:
                field_conditions.append(combine_conditions_or(or_sub_conditions))

        # Handle NOT logical operator
        if self.NOT:
            not_sub_conditions: list[QueryCondition] = []
            for sub_filter in self.NOT:
                not_sub_conditions.extend(sub_filter.build_conditions())
            if not_sub_conditions:
                field_conditions.append(negate_conditions(not_sub_conditions))

        return field_conditions


@strawberry.input(description="Order by specification for notification channels")
class NotificationChannelOrderBy(GQLOrderBy):
    field: NotificationChannelOrderField
    direction: OrderDirection = OrderDirection.ASC

    @override
    def to_query_order(self) -> QueryOrder:
        """Convert to repository QueryOrder."""
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case NotificationChannelOrderField.NAME:
                return NotificationChannelOrders.name(ascending)
            case NotificationChannelOrderField.CREATED_AT:
                return NotificationChannelOrders.created_at(ascending)
            case NotificationChannelOrderField.UPDATED_AT:
                return NotificationChannelOrders.updated_at(ascending)


@strawberry.enum
class NotificationRuleOrderField(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


@strawberry.input(description="Filter for notification rules")
class NotificationRuleFilter(GQLFilter):
    name: Optional[StringFilter] = None
    rule_type: Optional[list[NotificationRuleTypeGQL]] = None
    enabled: Optional[bool] = None

    AND: Optional[list[NotificationRuleFilter]] = None
    OR: Optional[list[NotificationRuleFilter]] = None
    NOT: Optional[list[NotificationRuleFilter]] = None

    @override
    def build_conditions(self) -> list[QueryCondition]:
        """Build query conditions from this filter.

        Returns a list containing a single combined QueryCondition that represents
        all filters with proper logical operators applied.
        """
        # Collect direct field conditions (these will be combined with AND)
        field_conditions: list[QueryCondition] = []

        # Apply name filter
        if self.name:
            name_condition = self.name.build_query_condition(
                contains_factory=NotificationRuleConditions.by_name_contains,
                equals_factory=NotificationRuleConditions.by_name_equals,
            )
            if name_condition:
                field_conditions.append(name_condition)

        # Apply rule_type filter
        if self.rule_type:
            internal_types = [rt.to_internal() for rt in self.rule_type]
            field_conditions.append(NotificationRuleConditions.by_rule_types(internal_types))

        # Apply enabled filter
        if self.enabled is not None:
            field_conditions.append(NotificationRuleConditions.by_enabled(self.enabled))

        # Handle AND logical operator - these are implicitly ANDed with field conditions
        if self.AND:
            for sub_filter in self.AND:
                field_conditions.extend(sub_filter.build_conditions())

        # Handle OR logical operator
        if self.OR:
            or_sub_conditions: list[QueryCondition] = []
            for sub_filter in self.OR:
                or_sub_conditions.extend(sub_filter.build_conditions())
            if or_sub_conditions:
                field_conditions.append(combine_conditions_or(or_sub_conditions))

        # Handle NOT logical operator
        if self.NOT:
            not_sub_conditions: list[QueryCondition] = []
            for sub_filter in self.NOT:
                not_sub_conditions.extend(sub_filter.build_conditions())
            if not_sub_conditions:
                field_conditions.append(negate_conditions(not_sub_conditions))

        return field_conditions


@strawberry.input(description="Order by specification for notification rules")
class NotificationRuleOrderBy(GQLOrderBy):
    field: NotificationRuleOrderField
    direction: OrderDirection = OrderDirection.ASC

    @override
    def to_query_order(self) -> QueryOrder:
        """Convert to repository QueryOrder."""
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case NotificationRuleOrderField.NAME:
                return NotificationRuleOrders.name(ascending)
            case NotificationRuleOrderField.CREATED_AT:
                return NotificationRuleOrders.created_at(ascending)
            case NotificationRuleOrderField.UPDATED_AT:
                return NotificationRuleOrders.updated_at(ascending)


# Input types for mutations


@strawberry.input(description="Input for webhook configuration")
class WebhookConfigInput:
    url: str

    def to_dataclass(self) -> WebhookConfig:
        return WebhookConfig(url=self.url)


@strawberry.input(description="Input for creating a notification channel")
class CreateNotificationChannelInput:
    name: str
    description: Optional[str] = None
    channel_type: NotificationChannelTypeGQL = NotificationChannelTypeGQL.WEBHOOK
    config: WebhookConfigInput = strawberry.field()
    enabled: bool = True

    def to_creator(self, created_by: uuid.UUID) -> Creator[NotificationChannelRow]:
        return Creator(
            spec=NotificationChannelCreatorSpec(
                name=self.name,
                description=self.description,
                channel_type=self.channel_type.to_internal(),
                config=self.config.to_dataclass(),
                enabled=self.enabled,
                created_by=created_by,
            )
        )


@strawberry.input(description="Input for updating a notification channel")
class UpdateNotificationChannelInput:
    id: ID
    name: Optional[str] = UNSET
    description: Optional[str] = UNSET
    config: Optional[WebhookConfigInput] = UNSET
    enabled: Optional[bool] = UNSET

    def to_updater(self, channel_id: uuid.UUID) -> Updater[NotificationChannelRow]:
        config_state = OptionalState[WebhookConfig].nop()
        if self.config is not UNSET:
            if self.config is None:
                config_state = OptionalState[WebhookConfig].nop()
            else:
                config_state = OptionalState[WebhookConfig].update(self.config.to_dataclass())

        spec = NotificationChannelUpdaterSpec(
            name=OptionalState[str].from_graphql(self.name),
            description=OptionalState[Optional[str]].from_graphql(self.description),
            config=config_state,
            enabled=OptionalState[bool].from_graphql(self.enabled),
        )
        return Updater(spec=spec, pk_value=channel_id)


@strawberry.input(description="Input for deleting a notification channel")
class DeleteNotificationChannelInput:
    id: ID


@strawberry.input(description="Input for creating a notification rule")
class CreateNotificationRuleInput:
    name: str
    description: Optional[str] = None
    rule_type: NotificationRuleTypeGQL = strawberry.field()
    channel_id: ID
    message_template: str
    enabled: bool = True

    def to_creator(self, created_by: uuid.UUID) -> Creator[NotificationRuleRow]:
        return Creator(
            spec=NotificationRuleCreatorSpec(
                name=self.name,
                description=self.description,
                rule_type=self.rule_type.to_internal(),
                channel_id=uuid.UUID(self.channel_id),
                message_template=self.message_template,
                enabled=self.enabled,
                created_by=created_by,
            )
        )


@strawberry.input(description="Input for updating a notification rule")
class UpdateNotificationRuleInput:
    id: ID
    name: Optional[str] = UNSET
    description: Optional[str] = UNSET
    message_template: Optional[str] = UNSET
    enabled: Optional[bool] = UNSET

    def to_updater(self, rule_id: uuid.UUID) -> Updater[NotificationRuleRow]:
        spec = NotificationRuleUpdaterSpec(
            name=OptionalState[str].from_graphql(self.name),
            description=OptionalState[Optional[str]].from_graphql(self.description),
            message_template=OptionalState[str].from_graphql(self.message_template),
            enabled=OptionalState[bool].from_graphql(self.enabled),
        )
        return Updater(spec=spec, pk_value=rule_id)


@strawberry.input(description="Input for deleting a notification rule")
class DeleteNotificationRuleInput:
    id: ID


# Payload types for mutations


@strawberry.type(description="Payload for create notification channel mutation")
class CreateNotificationChannelPayload:
    channel: NotificationChannel


@strawberry.type(description="Payload for update notification channel mutation")
class UpdateNotificationChannelPayload:
    channel: NotificationChannel


@strawberry.type(description="Payload for delete notification channel mutation")
class DeleteNotificationChannelPayload:
    id: ID


@strawberry.type(description="Payload for create notification rule mutation")
class CreateNotificationRulePayload:
    rule: NotificationRule


@strawberry.type(description="Payload for update notification rule mutation")
class UpdateNotificationRulePayload:
    rule: NotificationRule


@strawberry.type(description="Payload for delete notification rule mutation")
class DeleteNotificationRulePayload:
    id: ID


# Validate mutations


@strawberry.input(description="Input for validate notification channel mutation")
class ValidateNotificationChannelInput:
    id: ID
    test_message: str


@strawberry.type(description="Payload for validate notification channel mutation")
class ValidateNotificationChannelPayload:
    id: ID


@strawberry.input(description="Input for validate notification rule mutation")
class ValidateNotificationRuleInput:
    id: ID
    notification_data: Optional[strawberry.scalars.JSON] = UNSET


@strawberry.type(description="Payload for validate notification rule mutation")
class ValidateNotificationRulePayload:
    message: str
