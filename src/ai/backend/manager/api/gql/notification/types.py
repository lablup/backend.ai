"""GraphQL types, filters, and inputs for notification system."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Self, override

import strawberry
from strawberry import ID, UNSET
from strawberry.relay import Node, NodeID

from ai.backend.common.data.notification import (
    NotificationChannelType,
    NotificationRuleType,
    WebhookSpec,
)
from ai.backend.common.data.notification.types import (
    EmailMessage,
    EmailSpec,
    SMTPAuth,
    SMTPConnection,
)
from ai.backend.common.exception import InvalidNotificationChannelSpec
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
    EMAIL = "email"

    @classmethod
    def from_internal(cls, internal_type: NotificationChannelType) -> NotificationChannelTypeGQL:
        """Convert internal NotificationChannelType to GraphQL enum."""
        match internal_type:
            case NotificationChannelType.WEBHOOK:
                return cls.WEBHOOK
            case NotificationChannelType.EMAIL:
                return cls.EMAIL

    def to_internal(self) -> NotificationChannelType:
        """Convert GraphQL enum to internal NotificationChannelType."""
        match self:
            case NotificationChannelTypeGQL.WEBHOOK:
                return NotificationChannelType.WEBHOOK
            case NotificationChannelTypeGQL.EMAIL:
                return NotificationChannelType.EMAIL


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
@strawberry.interface(
    name="NotificationChannelSpec",
    description="Interface for notification channel specifications",
)
class NotificationChannelSpecGQL:
    channel_type: NotificationChannelTypeGQL


@strawberry.type(
    name="WebhookSpec",
    description="Specification for webhook notification channel",
)
class WebhookSpecGQL(NotificationChannelSpecGQL):
    url: str

    @classmethod
    def from_dataclass(cls, config: WebhookSpec) -> Self:
        return cls(
            channel_type=NotificationChannelTypeGQL.WEBHOOK,
            url=config.url,
        )


@strawberry.type(
    name="SMTPAuth",
    description="SMTP authentication credentials",
)
class SMTPAuthGQL:
    username: str | None


@strawberry.type(
    name="SMTPConnection",
    description="SMTP server connection settings",
)
class SMTPConnectionGQL:
    host: str
    port: int
    use_tls: bool
    timeout: int


@strawberry.type(
    name="EmailMessage",
    description="Email message settings",
)
class EmailMessageGQL:
    from_email: str
    to_emails: list[str]
    subject_template: str | None


@strawberry.type(
    name="EmailSpec",
    description="Specification for email notification channel",
)
class EmailSpecGQL(NotificationChannelSpecGQL):
    smtp: SMTPConnectionGQL
    message: EmailMessageGQL
    auth: SMTPAuthGQL | None

    @classmethod
    def from_dataclass(cls, config: EmailSpec) -> Self:
        return cls(
            channel_type=NotificationChannelTypeGQL.EMAIL,
            smtp=SMTPConnectionGQL(
                host=config.smtp.host,
                port=config.smtp.port,
                use_tls=config.smtp.use_tls,
                timeout=config.smtp.timeout,
            ),
            auth=SMTPAuthGQL(username=config.auth.username) if config.auth is not None else None,
            message=EmailMessageGQL(
                from_email=config.message.from_email,
                to_emails=config.message.to_emails,
                subject_template=config.message.subject_template,
            ),
        )


@strawberry.type(description="Notification channel")
class NotificationChannel(Node):
    id: NodeID[str]
    name: str
    description: str | None
    channel_type: NotificationChannelTypeGQL
    spec: NotificationChannelSpecGQL
    enabled: bool
    created_at: datetime

    @classmethod
    def from_dataclass(cls, data: NotificationChannelData) -> Self:
        final_spec: NotificationChannelSpecGQL
        match data.channel_type:
            case NotificationChannelType.WEBHOOK:
                if not isinstance(data.spec, WebhookSpec):
                    raise InvalidNotificationChannelSpec(
                        f"Expected WebhookSpec for WEBHOOK channel, got {type(data.spec).__name__}"
                    )
                final_spec = WebhookSpecGQL.from_dataclass(data.spec)
            case NotificationChannelType.EMAIL:
                if not isinstance(data.spec, EmailSpec):
                    raise InvalidNotificationChannelSpec(
                        f"Expected EmailSpec for EMAIL channel, got {type(data.spec).__name__}"
                    )
                final_spec = EmailSpecGQL.from_dataclass(data.spec)
        return cls(
            id=ID(str(data.id)),
            name=data.name,
            description=data.description,
            channel_type=NotificationChannelTypeGQL.from_internal(data.channel_type),
            spec=final_spec,
            enabled=data.enabled,
            created_at=data.created_at,
        )


@strawberry.type(description="Notification rule")
class NotificationRule(Node):
    id: NodeID[str]
    name: str
    description: str | None
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
    name: StringFilter | None = None
    channel_type: list[NotificationChannelTypeGQL] | None = None
    enabled: bool | None = None

    AND: list[NotificationChannelFilter] | None = None
    OR: list[NotificationChannelFilter] | None = None
    NOT: list[NotificationChannelFilter] | None = None

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
                starts_with_factory=NotificationChannelConditions.by_name_starts_with,
                ends_with_factory=NotificationChannelConditions.by_name_ends_with,
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
    name: StringFilter | None = None
    rule_type: list[NotificationRuleTypeGQL] | None = None
    enabled: bool | None = None

    AND: list[NotificationRuleFilter] | None = None
    OR: list[NotificationRuleFilter] | None = None
    NOT: list[NotificationRuleFilter] | None = None

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
                starts_with_factory=NotificationRuleConditions.by_name_starts_with,
                ends_with_factory=NotificationRuleConditions.by_name_ends_with,
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
class WebhookSpecInput:
    url: str

    def to_dataclass(self) -> WebhookSpec:
        return WebhookSpec(url=self.url)


@strawberry.input(description="Input for SMTP authentication credentials")
class SMTPAuthInput:
    username: str | None = None
    password: str | None = None

    def to_dataclass(self) -> SMTPAuth:
        return SMTPAuth(username=self.username, password=self.password)


@strawberry.input(description="Input for SMTP server connection settings")
class SMTPConnectionInput:
    host: str
    port: int
    use_tls: bool = True
    timeout: int = 30

    def to_dataclass(self) -> SMTPConnection:
        return SMTPConnection(
            host=self.host,
            port=self.port,
            use_tls=self.use_tls,
            timeout=self.timeout,
        )


@strawberry.input(description="Input for email message settings")
class EmailMessageInput:
    from_email: str
    to_emails: list[str]
    subject_template: str | None = None

    def to_dataclass(self) -> EmailMessage:
        return EmailMessage(
            from_email=self.from_email,
            to_emails=self.to_emails,
            subject_template=self.subject_template,
        )


@strawberry.input(description="Input for email notification channel configuration")
class EmailSpecInput:
    smtp: SMTPConnectionInput
    message: EmailMessageInput
    auth: SMTPAuthInput | None = None

    def to_dataclass(self) -> EmailSpec:
        return EmailSpec(
            smtp=self.smtp.to_dataclass(),
            message=self.message.to_dataclass(),
            auth=self.auth.to_dataclass() if self.auth else None,
        )


@strawberry.input(
    description="Input for notification channel configuration. Exactly one of webhook or email must be set.",
    one_of=True,
)
class NotificationChannelSpecInput:
    webhook: WebhookSpecInput | None = UNSET
    email: EmailSpecInput | None = UNSET

    def to_dataclass(self) -> WebhookSpec | EmailSpec:
        """Convert to the appropriate dataclass based on which field is set."""
        if self.webhook is not None and self.webhook is not UNSET:
            return self.webhook.to_dataclass()
        if self.email is not None and self.email is not UNSET:
            return self.email.to_dataclass()
        raise InvalidNotificationChannelSpec("Exactly one of webhook or email must be set")

    def get_channel_type(self) -> NotificationChannelType:
        """Get the channel type based on which field is set."""
        if self.webhook is not None and self.webhook is not UNSET:
            return NotificationChannelType.WEBHOOK
        if self.email is not None and self.email is not UNSET:
            return NotificationChannelType.EMAIL
        raise InvalidNotificationChannelSpec("Exactly one of webhook or email must be set")


@strawberry.input(description="Input for creating a notification channel")
class CreateNotificationChannelInput:
    name: str
    description: str | None = None
    channel_type: NotificationChannelTypeGQL
    spec: NotificationChannelSpecInput
    enabled: bool = True

    def to_creator(self, created_by: uuid.UUID) -> Creator[NotificationChannelRow]:
        return Creator(
            spec=NotificationChannelCreatorSpec(
                name=self.name,
                description=self.description,
                channel_type=self.channel_type.to_internal(),
                spec=self.spec.to_dataclass(),
                enabled=self.enabled,
                created_by=created_by,
            )
        )


@strawberry.input(description="Input for updating a notification channel")
class UpdateNotificationChannelInput:
    id: ID
    name: str | None = UNSET
    description: str | None = UNSET
    spec: NotificationChannelSpecInput | None = UNSET
    enabled: bool | None = UNSET

    def to_updater(self, channel_id: uuid.UUID) -> Updater[NotificationChannelRow]:
        spec_state = OptionalState[WebhookSpec | EmailSpec].nop()
        if self.spec is not UNSET:
            if self.spec is None:
                spec_state = OptionalState[WebhookSpec | EmailSpec].nop()
            else:
                spec_state = OptionalState[WebhookSpec | EmailSpec].update(self.spec.to_dataclass())

        updater_spec = NotificationChannelUpdaterSpec(
            name=OptionalState[str].from_graphql(self.name),
            description=OptionalState[str | None].from_graphql(self.description),
            spec=spec_state,
            enabled=OptionalState[bool].from_graphql(self.enabled),
        )
        return Updater(spec=updater_spec, pk_value=channel_id)


@strawberry.input(description="Input for deleting a notification channel")
class DeleteNotificationChannelInput:
    id: ID


@strawberry.input(description="Input for creating a notification rule")
class CreateNotificationRuleInput:
    name: str
    description: str | None = None
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
    name: str | None = UNSET
    description: str | None = UNSET
    message_template: str | None = UNSET
    enabled: bool | None = UNSET

    def to_updater(self, rule_id: uuid.UUID) -> Updater[NotificationRuleRow]:
        spec = NotificationRuleUpdaterSpec(
            name=OptionalState[str].from_graphql(self.name),
            description=OptionalState[str | None].from_graphql(self.description),
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
    notification_data: strawberry.scalars.JSON | None = UNSET


@strawberry.type(description="Payload for validate notification rule mutation")
class ValidateNotificationRulePayload:
    message: str
