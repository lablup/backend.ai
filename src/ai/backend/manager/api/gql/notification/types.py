"""GraphQL types, filters, and inputs for notification system."""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from typing import Any, Self

import strawberry
from strawberry import ID, UNSET, Info
from strawberry.relay import NodeID

from ai.backend.common.api_handlers import SENTINEL
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
from ai.backend.common.dto.manager.v2.notification.request import (
    CreateNotificationChannelInput as CreateNotificationChannelInputDTO,
)
from ai.backend.common.dto.manager.v2.notification.request import (
    CreateNotificationRuleInput as CreateNotificationRuleInputDTO,
)
from ai.backend.common.dto.manager.v2.notification.request import (
    DeleteNotificationChannelInput as DeleteNotificationChannelInputDTO,
)
from ai.backend.common.dto.manager.v2.notification.request import (
    DeleteNotificationRuleInput as DeleteNotificationRuleInputDTO,
)
from ai.backend.common.dto.manager.v2.notification.request import (
    EmailMessageInputDTO,
    EmailSpecInputDTO,
    NotificationChannelSpecInputDTO,
    SMTPAuthInputDTO,
    SMTPConnectionInputDTO,
    WebhookSpecInputDTO,
)
from ai.backend.common.dto.manager.v2.notification.request import (
    NotificationChannelFilter as NotificationChannelFilterDTO,
)
from ai.backend.common.dto.manager.v2.notification.request import (
    NotificationChannelOrder as NotificationChannelOrderDTO,
)
from ai.backend.common.dto.manager.v2.notification.request import (
    NotificationChannelTypeFilter as NotificationChannelTypeFilterDTO,
)
from ai.backend.common.dto.manager.v2.notification.request import (
    NotificationRuleFilter as NotificationRuleFilterDTO,
)
from ai.backend.common.dto.manager.v2.notification.request import (
    NotificationRuleOrder as NotificationRuleOrderDTO,
)
from ai.backend.common.dto.manager.v2.notification.request import (
    NotificationRuleTypeFilter as NotificationRuleTypeFilterDTO,
)
from ai.backend.common.dto.manager.v2.notification.request import (
    UpdateNotificationChannelInput as UpdateNotificationChannelInputDTO,
)
from ai.backend.common.dto.manager.v2.notification.request import (
    UpdateNotificationRuleInput as UpdateNotificationRuleInputDTO,
)
from ai.backend.common.dto.manager.v2.notification.request import (
    ValidateNotificationChannelInput as ValidateNotificationChannelInputDTO,
)
from ai.backend.common.dto.manager.v2.notification.request import (
    ValidateNotificationRuleInput as ValidateNotificationRuleInputDTO,
)
from ai.backend.common.dto.manager.v2.notification.response import (
    CreateNotificationChannelPayload as CreateNotificationChannelPayloadDTO,
)
from ai.backend.common.dto.manager.v2.notification.response import (
    CreateNotificationRulePayload as CreateNotificationRulePayloadDTO,
)
from ai.backend.common.dto.manager.v2.notification.response import (
    DeleteNotificationChannelPayload as DeleteNotificationChannelPayloadDTO,
)
from ai.backend.common.dto.manager.v2.notification.response import (
    DeleteNotificationRulePayload as DeleteNotificationRulePayloadDTO,
)
from ai.backend.common.dto.manager.v2.notification.response import (
    NotificationChannelNode,
    NotificationRuleNode,
)
from ai.backend.common.dto.manager.v2.notification.response import (
    UpdateNotificationChannelPayload as UpdateNotificationChannelPayloadDTO,
)
from ai.backend.common.dto.manager.v2.notification.response import (
    UpdateNotificationRulePayload as UpdateNotificationRulePayloadDTO,
)
from ai.backend.common.dto.manager.v2.notification.response import (
    ValidateNotificationRulePayload as ValidateNotificationRulePayloadDTO,
)
from ai.backend.common.dto.manager.v2.notification.types import (
    EmailSpecInfo,
    WebhookSpecInfo,
)
from ai.backend.common.dto.manager.v2.notification.types import (
    NotificationChannelOrderField as NotificationChannelOrderFieldDTO,
)
from ai.backend.common.dto.manager.v2.notification.types import (
    NotificationRuleOrderField as NotificationRuleOrderFieldDTO,
)
from ai.backend.common.dto.manager.v2.notification.types import (
    OrderDirection as OrderDirectionDTO,
)
from ai.backend.common.exception import InvalidNotificationChannelSpec
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.data.notification import (
    NotificationChannelData,
    NotificationRuleData,
)

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
    ENDPOINT_LIFECYCLE_CHANGED = "endpoint.lifecycle.changed"

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
            case NotificationRuleType.ENDPOINT_LIFECYCLE_CHANGED:
                return cls.ENDPOINT_LIFECYCLE_CHANGED

    def to_internal(self) -> NotificationRuleType:
        """Convert GraphQL enum to internal NotificationRuleType."""
        match self:
            case NotificationRuleTypeGQL.SESSION_STARTED:
                return NotificationRuleType.SESSION_STARTED
            case NotificationRuleTypeGQL.SESSION_TERMINATED:
                return NotificationRuleType.SESSION_TERMINATED
            case NotificationRuleTypeGQL.ARTIFACT_DOWNLOAD_COMPLETED:
                return NotificationRuleType.ARTIFACT_DOWNLOAD_COMPLETED
            case NotificationRuleTypeGQL.ENDPOINT_LIFECYCLE_CHANGED:
                return NotificationRuleType.ENDPOINT_LIFECYCLE_CHANGED


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
class NotificationChannel(PydanticNodeMixin[NotificationChannelNode]):
    id: NodeID[str]
    name: str
    description: str | None
    channel_type: NotificationChannelTypeGQL
    spec: NotificationChannelSpecGQL
    enabled: bool
    created_at: datetime

    @classmethod
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.notification_channel_loader.load_many([
            uuid.UUID(nid) for nid in node_ids
        ])
        return [cls.from_dataclass(data) if data is not None else None for data in results]

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

    @classmethod
    def from_pydantic(
        cls,
        dto: NotificationChannelNode,
        *,
        id_field: str = "id",
        extra: dict[str, Any] | None = None,
    ) -> Self:
        final_spec: NotificationChannelSpecGQL
        match dto.channel_type:
            case NotificationChannelType.WEBHOOK:
                if not isinstance(dto.spec, WebhookSpecInfo):
                    raise InvalidNotificationChannelSpec(
                        f"Expected WebhookSpecInfo for WEBHOOK channel, got {type(dto.spec).__name__}"
                    )
                final_spec = WebhookSpecGQL(
                    channel_type=NotificationChannelTypeGQL.WEBHOOK,
                    url=dto.spec.url,
                )
            case NotificationChannelType.EMAIL:
                if not isinstance(dto.spec, EmailSpecInfo):
                    raise InvalidNotificationChannelSpec(
                        f"Expected EmailSpecInfo for EMAIL channel, got {type(dto.spec).__name__}"
                    )
                final_spec = EmailSpecGQL(
                    channel_type=NotificationChannelTypeGQL.EMAIL,
                    smtp=SMTPConnectionGQL(
                        host=dto.spec.smtp_host,
                        port=dto.spec.smtp_port,
                        use_tls=dto.spec.smtp_use_tls,
                        timeout=dto.spec.smtp_timeout,
                    ),
                    message=EmailMessageGQL(
                        from_email=dto.spec.from_email,
                        to_emails=dto.spec.to_emails,
                        subject_template=dto.spec.subject_template,
                    ),
                    auth=(
                        SMTPAuthGQL(username=dto.spec.auth_username)
                        if dto.spec.auth_username is not None
                        else None
                    ),
                )
        return cls(
            id=ID(str(dto.id)),
            name=dto.name,
            description=dto.description,
            channel_type=NotificationChannelTypeGQL.from_internal(dto.channel_type),
            spec=final_spec,
            enabled=dto.enabled,
            created_at=dto.created_at,
        )


@strawberry.type(description="Notification rule")
class NotificationRule(PydanticNodeMixin[NotificationRuleNode]):
    id: NodeID[str]
    name: str
    description: str | None
    rule_type: NotificationRuleTypeGQL
    channel: NotificationChannel
    message_template: str
    enabled: bool
    created_at: datetime

    @classmethod
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.notification_rule_loader.load_many([
            uuid.UUID(nid) for nid in node_ids
        ])
        return [cls.from_dataclass(data) if data is not None else None for data in results]

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

    @classmethod
    def from_pydantic(
        cls,
        dto: NotificationRuleNode,
        *,
        id_field: str = "id",
        extra: dict[str, Any] | None = None,
    ) -> Self:
        return cls(
            id=ID(str(dto.id)),
            name=dto.name,
            description=dto.description,
            rule_type=NotificationRuleTypeGQL.from_internal(dto.rule_type),
            channel=NotificationChannel.from_pydantic(dto.channel),
            message_template=dto.message_template,
            enabled=dto.enabled,
            created_at=dto.created_at,
        )


# Filter and OrderBy types


@strawberry.enum
class NotificationChannelOrderField(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


@strawberry.experimental.pydantic.input(
    model=NotificationChannelTypeFilterDTO,
    name="NotificationChannelTypeFilter",
    description="Added in 26.3.0. Filter for notification channel type with equality and membership operators.",
)
class NotificationChannelTypeFilterGQL:
    equals: NotificationChannelTypeGQL | None = strawberry.field(
        default=None, description="Matches channels with this exact type."
    )
    in_: list[NotificationChannelTypeGQL] | None = strawberry.field(
        name="in", default=None, description="Matches channels whose type is in this list."
    )
    not_equals: NotificationChannelTypeGQL | None = strawberry.field(
        default=None, description="Excludes channels with this exact type."
    )
    not_in: list[NotificationChannelTypeGQL] | None = strawberry.field(
        default=None, description="Excludes channels whose type is in this list."
    )

    def to_pydantic(self) -> NotificationChannelTypeFilterDTO:
        return NotificationChannelTypeFilterDTO(
            equals=self.equals.to_internal() if self.equals is not None else None,
            in_=[t.to_internal() for t in self.in_] if self.in_ is not None else None,
            not_equals=self.not_equals.to_internal() if self.not_equals is not None else None,
            not_in=[t.to_internal() for t in self.not_in] if self.not_in is not None else None,
        )


@strawberry.experimental.pydantic.input(
    model=NotificationChannelFilterDTO,
    name="NotificationChannelFilter",
    description="Filter for notification channels",
)
class NotificationChannelFilter:
    name: StringFilter | None = None
    channel_type: NotificationChannelTypeFilterGQL | None = None
    enabled: bool | None = None

    AND: list[NotificationChannelFilter] | None = None
    OR: list[NotificationChannelFilter] | None = None
    NOT: list[NotificationChannelFilter] | None = None

    def to_pydantic(self) -> NotificationChannelFilterDTO:
        return NotificationChannelFilterDTO(
            name=self.name.to_pydantic() if self.name is not None else None,
            channel_type=(
                self.channel_type.to_pydantic() if self.channel_type is not None else None
            ),
            enabled=self.enabled,
            AND=[f.to_pydantic() for f in self.AND] if self.AND is not None else None,
            OR=[f.to_pydantic() for f in self.OR] if self.OR is not None else None,
            NOT=[f.to_pydantic() for f in self.NOT] if self.NOT is not None else None,
        )


@strawberry.experimental.pydantic.input(
    model=NotificationChannelOrderDTO,
    name="NotificationChannelOrderBy",
    description="Order by specification for notification channels",
)
class NotificationChannelOrderBy:
    field: NotificationChannelOrderField
    direction: OrderDirection = OrderDirection.ASC

    def to_pydantic(self) -> NotificationChannelOrderDTO:
        return NotificationChannelOrderDTO(
            field=NotificationChannelOrderFieldDTO(self.field.value),
            direction=OrderDirectionDTO(self.direction.value),
        )


@strawberry.enum
class NotificationRuleOrderField(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


@strawberry.experimental.pydantic.input(
    model=NotificationRuleTypeFilterDTO,
    name="NotificationRuleTypeFilter",
    description="Added in 26.3.0. Filter for notification rule type with equality and membership operators.",
)
class NotificationRuleTypeFilterGQL:
    equals: NotificationRuleTypeGQL | None = strawberry.field(
        default=None, description="Matches rules with this exact type."
    )
    in_: list[NotificationRuleTypeGQL] | None = strawberry.field(
        name="in", default=None, description="Matches rules whose type is in this list."
    )
    not_equals: NotificationRuleTypeGQL | None = strawberry.field(
        default=None, description="Excludes rules with this exact type."
    )
    not_in: list[NotificationRuleTypeGQL] | None = strawberry.field(
        default=None, description="Excludes rules whose type is in this list."
    )

    def to_pydantic(self) -> NotificationRuleTypeFilterDTO:
        return NotificationRuleTypeFilterDTO(
            equals=self.equals.to_internal() if self.equals is not None else None,
            in_=[t.to_internal() for t in self.in_] if self.in_ is not None else None,
            not_equals=self.not_equals.to_internal() if self.not_equals is not None else None,
            not_in=[t.to_internal() for t in self.not_in] if self.not_in is not None else None,
        )


@strawberry.experimental.pydantic.input(
    model=NotificationRuleFilterDTO,
    name="NotificationRuleFilter",
    description="Filter for notification rules",
)
class NotificationRuleFilter:
    name: StringFilter | None = None
    rule_type: NotificationRuleTypeFilterGQL | None = None
    enabled: bool | None = None

    AND: list[NotificationRuleFilter] | None = None
    OR: list[NotificationRuleFilter] | None = None
    NOT: list[NotificationRuleFilter] | None = None

    def to_pydantic(self) -> NotificationRuleFilterDTO:
        return NotificationRuleFilterDTO(
            name=self.name.to_pydantic() if self.name is not None else None,
            rule_type=self.rule_type.to_pydantic() if self.rule_type is not None else None,
            enabled=self.enabled,
            AND=[f.to_pydantic() for f in self.AND] if self.AND is not None else None,
            OR=[f.to_pydantic() for f in self.OR] if self.OR is not None else None,
            NOT=[f.to_pydantic() for f in self.NOT] if self.NOT is not None else None,
        )


@strawberry.experimental.pydantic.input(
    model=NotificationRuleOrderDTO,
    name="NotificationRuleOrderBy",
    description="Order by specification for notification rules",
)
class NotificationRuleOrderBy:
    field: NotificationRuleOrderField
    direction: OrderDirection = OrderDirection.ASC

    def to_pydantic(self) -> NotificationRuleOrderDTO:
        return NotificationRuleOrderDTO(
            field=NotificationRuleOrderFieldDTO(self.field.value),
            direction=OrderDirectionDTO(self.direction.value),
        )


# Input types for mutations


@strawberry.experimental.pydantic.input(
    model=WebhookSpecInputDTO,
    name="WebhookSpecInput",
    description="Input for webhook configuration",
)
class WebhookSpecInput:
    url: str

    def to_dataclass(self) -> WebhookSpec:
        return WebhookSpec(url=self.url)

    def to_pydantic(self) -> WebhookSpecInputDTO:
        return WebhookSpecInputDTO(url=self.url)


@strawberry.experimental.pydantic.input(
    model=SMTPAuthInputDTO,
    name="SMTPAuthInput",
    description="Input for SMTP authentication credentials",
)
class SMTPAuthInput:
    username: str | None = None
    password: str | None = None

    def to_dataclass(self) -> SMTPAuth:
        return SMTPAuth(username=self.username, password=self.password)

    def to_pydantic(self) -> SMTPAuthInputDTO:
        return SMTPAuthInputDTO(username=self.username, password=self.password)


@strawberry.experimental.pydantic.input(
    model=SMTPConnectionInputDTO,
    name="SMTPConnectionInput",
    description="Input for SMTP server connection settings",
)
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

    def to_pydantic(self) -> SMTPConnectionInputDTO:
        return SMTPConnectionInputDTO(
            host=self.host,
            port=self.port,
            use_tls=self.use_tls,
            timeout=self.timeout,
        )


@strawberry.experimental.pydantic.input(
    model=EmailMessageInputDTO,
    name="EmailMessageInput",
    description="Input for email message settings",
)
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

    def to_pydantic(self) -> EmailMessageInputDTO:
        return EmailMessageInputDTO(
            from_email=self.from_email,
            to_emails=self.to_emails,
            subject_template=self.subject_template,
        )


@strawberry.experimental.pydantic.input(
    model=EmailSpecInputDTO,
    name="EmailSpecInput",
    description="Input for email notification channel configuration",
)
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

    def to_pydantic(self) -> EmailSpecInputDTO:
        return EmailSpecInputDTO(
            smtp=self.smtp.to_pydantic(),
            message=self.message.to_pydantic(),
            auth=self.auth.to_pydantic() if self.auth else None,
        )


@strawberry.experimental.pydantic.input(
    model=NotificationChannelSpecInputDTO,
    name="NotificationChannelSpecInput",
    description="Input for notification channel configuration. Exactly one of webhook or email must be set.",
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

    def to_pydantic(self) -> NotificationChannelSpecInputDTO:
        return NotificationChannelSpecInputDTO(
            webhook=self.webhook.to_pydantic()
            if (self.webhook is not None and self.webhook is not UNSET)
            else None,
            email=self.email.to_pydantic()
            if (self.email is not None and self.email is not UNSET)
            else None,
        )


@strawberry.experimental.pydantic.input(
    model=CreateNotificationChannelInputDTO,
    description="Input for creating a notification channel",
)
class CreateNotificationChannelInput:
    name: str
    description: str | None = None
    channel_type: NotificationChannelTypeGQL
    spec: NotificationChannelSpecInput
    enabled: bool = True

    def to_pydantic(self) -> CreateNotificationChannelInputDTO:
        return CreateNotificationChannelInputDTO(
            name=self.name,
            description=self.description,
            channel_type=self.channel_type.to_internal(),
            spec=self.spec.to_dataclass(),
            enabled=self.enabled,
        )


@strawberry.experimental.pydantic.input(
    model=UpdateNotificationChannelInputDTO,
    description="Input for updating a notification channel",
)
class UpdateNotificationChannelInput:
    id: ID
    name: str | None = UNSET
    description: str | None = UNSET
    spec: NotificationChannelSpecInput | None = UNSET
    enabled: bool | None = UNSET

    def to_pydantic(self) -> UpdateNotificationChannelInputDTO:
        return UpdateNotificationChannelInputDTO(
            name=None if self.name is UNSET else self.name,
            description=SENTINEL if self.description is UNSET else self.description,
            spec=(None if (self.spec is UNSET or self.spec is None) else self.spec.to_dataclass()),
            enabled=None if self.enabled is UNSET else self.enabled,
        )


@strawberry.experimental.pydantic.input(
    model=DeleteNotificationChannelInputDTO,
    description="Input for deleting a notification channel",
)
class DeleteNotificationChannelInput:
    id: ID


@strawberry.experimental.pydantic.input(
    model=CreateNotificationRuleInputDTO,
    description="Input for creating a notification rule",
)
class CreateNotificationRuleInput:
    name: str
    description: str | None = None
    rule_type: NotificationRuleTypeGQL = strawberry.field()
    channel_id: ID
    message_template: str
    enabled: bool = True


@strawberry.experimental.pydantic.input(
    model=UpdateNotificationRuleInputDTO,
    description="Input for updating a notification rule",
)
class UpdateNotificationRuleInput:
    id: ID
    name: str | None = UNSET
    description: str | None = UNSET
    message_template: str | None = UNSET
    enabled: bool | None = UNSET

    def to_pydantic(self) -> UpdateNotificationRuleInputDTO:
        return UpdateNotificationRuleInputDTO(
            name=None if self.name is UNSET else self.name,
            description=SENTINEL if self.description is UNSET else self.description,
            message_template=None if self.message_template is UNSET else self.message_template,
            enabled=None if self.enabled is UNSET else self.enabled,
        )


@strawberry.experimental.pydantic.input(
    model=DeleteNotificationRuleInputDTO,
    description="Input for deleting a notification rule",
)
class DeleteNotificationRuleInput:
    id: ID


# Payload types for mutations


@strawberry.type(description="Payload for create notification channel mutation")
class CreateNotificationChannelPayload:
    channel: NotificationChannel

    @classmethod
    def from_pydantic(cls, dto: CreateNotificationChannelPayloadDTO) -> Self:
        return cls(channel=NotificationChannel.from_pydantic(dto.channel))


@strawberry.type(description="Payload for update notification channel mutation")
class UpdateNotificationChannelPayload:
    channel: NotificationChannel

    @classmethod
    def from_pydantic(cls, dto: UpdateNotificationChannelPayloadDTO) -> Self:
        return cls(channel=NotificationChannel.from_pydantic(dto.channel))


@strawberry.experimental.pydantic.type(
    model=DeleteNotificationChannelPayloadDTO,
    description="Payload for delete notification channel mutation",
    all_fields=True,
)
class DeleteNotificationChannelPayload:
    """Payload for notification channel deletion mutation."""


@strawberry.type(description="Payload for create notification rule mutation")
class CreateNotificationRulePayload:
    rule: NotificationRule

    @classmethod
    def from_pydantic(cls, dto: CreateNotificationRulePayloadDTO) -> Self:
        return cls(rule=NotificationRule.from_pydantic(dto.rule))


@strawberry.type(description="Payload for update notification rule mutation")
class UpdateNotificationRulePayload:
    rule: NotificationRule

    @classmethod
    def from_pydantic(cls, dto: UpdateNotificationRulePayloadDTO) -> Self:
        return cls(rule=NotificationRule.from_pydantic(dto.rule))


@strawberry.experimental.pydantic.type(
    model=DeleteNotificationRulePayloadDTO,
    description="Payload for delete notification rule mutation",
    all_fields=True,
)
class DeleteNotificationRulePayload:
    """Payload for notification rule deletion mutation."""


# Validate mutations


@strawberry.experimental.pydantic.input(
    model=ValidateNotificationChannelInputDTO,
    description="Input for validate notification channel mutation",
)
class ValidateNotificationChannelInput:
    id: ID
    test_message: str

    def to_pydantic(self) -> ValidateNotificationChannelInputDTO:
        return ValidateNotificationChannelInputDTO(
            id=uuid.UUID(self.id),
            test_message=self.test_message,
        )


@strawberry.type(description="Payload for validate notification channel mutation")
class ValidateNotificationChannelPayload:
    id: ID


@strawberry.experimental.pydantic.input(
    model=ValidateNotificationRuleInputDTO,
    description="Input for validate notification rule mutation",
)
class ValidateNotificationRuleInput:
    id: ID
    notification_data: strawberry.scalars.JSON | None = UNSET

    def to_pydantic(self) -> ValidateNotificationRuleInputDTO:
        return ValidateNotificationRuleInputDTO(
            id=uuid.UUID(self.id),
            notification_data={}
            if (self.notification_data is UNSET or self.notification_data is None)
            else dict(self.notification_data),
        )


@strawberry.experimental.pydantic.type(
    model=ValidateNotificationRulePayloadDTO,
    description="Payload for validate notification rule mutation",
    all_fields=True,
)
class ValidateNotificationRulePayload:
    """Payload for notification rule validation mutation."""
