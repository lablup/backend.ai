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
from ai.backend.common.data.notification import WebhookSpec
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
    ValidateNotificationChannelPayload as ValidateNotificationChannelPayloadDTO,
)
from ai.backend.common.dto.manager.v2.notification.response import (
    ValidateNotificationRulePayload as ValidateNotificationRulePayloadDTO,
)
from ai.backend.common.dto.manager.v2.notification.types import (
    EmailSpecInfo,
    NotificationChannelTypeDTO,
    NotificationRuleTypeDTO,
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
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_from_pydantic_type,
    gql_node_type,
    gql_output_type,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin, PydanticOutputMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext

# GraphQL enum types

NotificationChannelTypeGQL = strawberry.enum(
    NotificationChannelTypeDTO,
    name="NotificationChannelType",
    description="Notification channel types",
)

NotificationRuleTypeGQL = strawberry.enum(
    NotificationRuleTypeDTO,
    name="NotificationRuleType",
    description="Notification rule types",
)


# GraphQL object types
@strawberry.interface(
    name="NotificationChannelSpec",
    description="Interface for notification channel specifications",
)
class NotificationChannelSpecGQL:
    channel_type: NotificationChannelTypeGQL


@gql_output_type(
    BackendAIGQLMeta(
        added_version="26.3.0", description="Specification for webhook notification channel."
    ),
    name="WebhookSpec",
)
class WebhookSpecGQL(NotificationChannelSpecGQL):
    url: str


@gql_output_type(
    BackendAIGQLMeta(added_version="26.3.0", description="SMTP authentication credentials."),
    name="SMTPAuth",
)
class SMTPAuthGQL:
    username: str | None


@gql_output_type(
    BackendAIGQLMeta(added_version="26.3.0", description="SMTP server connection settings."),
    name="SMTPConnection",
)
class SMTPConnectionGQL:
    host: str
    port: int
    use_tls: bool
    timeout: int


@gql_output_type(
    BackendAIGQLMeta(added_version="26.3.0", description="Email message settings."),
    name="EmailMessage",
)
class EmailMessageGQL:
    from_email: str
    to_emails: list[str]
    subject_template: str | None


@gql_output_type(
    BackendAIGQLMeta(
        added_version="26.3.0", description="Specification for email notification channel."
    ),
    name="EmailSpec",
)
class EmailSpecGQL(NotificationChannelSpecGQL):
    smtp: SMTPConnectionGQL
    message: EmailMessageGQL
    auth: SMTPAuthGQL | None


@gql_node_type(BackendAIGQLMeta(added_version="26.3.0", description="Notification channel."))
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
    ) -> Iterable[NotificationChannel | None]:
        return await info.context.data_loaders.notification_channel_loader.load_many([
            uuid.UUID(nid) for nid in node_ids
        ])

    @classmethod
    def from_pydantic(
        cls,
        dto: NotificationChannelNode,
        extra: dict[str, Any] | None = None,
        *,
        id_field: str = "id",
    ) -> Self:
        final_spec: NotificationChannelSpecGQL
        match dto.channel_type:
            case NotificationChannelTypeDTO.WEBHOOK:
                if not isinstance(dto.spec, WebhookSpecInfo):
                    raise InvalidNotificationChannelSpec(
                        f"Expected WebhookSpecInfo for WEBHOOK channel, got {type(dto.spec).__name__}"
                    )
                final_spec = WebhookSpecGQL(
                    channel_type=NotificationChannelTypeDTO.WEBHOOK,
                    url=dto.spec.url,
                )
            case NotificationChannelTypeDTO.EMAIL:
                if not isinstance(dto.spec, EmailSpecInfo):
                    raise InvalidNotificationChannelSpec(
                        f"Expected EmailSpecInfo for EMAIL channel, got {type(dto.spec).__name__}"
                    )
                final_spec = EmailSpecGQL(
                    channel_type=NotificationChannelTypeDTO.EMAIL,
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
            channel_type=dto.channel_type,
            spec=final_spec,
            enabled=dto.enabled,
            created_at=dto.created_at,
        )


@gql_node_type(BackendAIGQLMeta(added_version="26.3.0", description="Notification rule."))
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
    ) -> Iterable[NotificationRule | None]:
        return await info.context.data_loaders.notification_rule_loader.load_many([
            uuid.UUID(nid) for nid in node_ids
        ])

    @classmethod
    def from_pydantic(
        cls,
        dto: NotificationRuleNode,
        extra: dict[str, Any] | None = None,
        *,
        id_field: str = "id",
    ) -> Self:
        return cls(
            id=ID(str(dto.id)),
            name=dto.name,
            description=dto.description,
            rule_type=dto.rule_type,
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


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter for notification channel type with equality and membership operators.",
        added_version="26.3.0",
    ),
    model=NotificationChannelTypeFilterDTO,
    name="NotificationChannelTypeFilter",
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
            equals=self.equals if self.equals is not None else None,
            in_=list(self.in_) if self.in_ is not None else None,
            not_equals=self.not_equals if self.not_equals is not None else None,
            not_in=list(self.not_in) if self.not_in is not None else None,
        )


@gql_pydantic_input(
    BackendAIGQLMeta(description="Filter for notification channels", added_version="24.09.0"),
    model=NotificationChannelFilterDTO,
    name="NotificationChannelFilter",
)
class NotificationChannelFilter:
    name: StringFilter | None = None
    channel_type: NotificationChannelTypeFilterGQL | None = None
    enabled: bool | None = None

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None

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


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Order by specification for notification channels", added_version="24.09.0"
    ),
    model=NotificationChannelOrderDTO,
    name="NotificationChannelOrderBy",
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


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter for notification rule type with equality and membership operators.",
        added_version="26.3.0",
    ),
    model=NotificationRuleTypeFilterDTO,
    name="NotificationRuleTypeFilter",
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
            equals=self.equals if self.equals is not None else None,
            in_=list(self.in_) if self.in_ is not None else None,
            not_equals=self.not_equals if self.not_equals is not None else None,
            not_in=list(self.not_in) if self.not_in is not None else None,
        )


@gql_pydantic_input(
    BackendAIGQLMeta(description="Filter for notification rules", added_version="24.09.0"),
    model=NotificationRuleFilterDTO,
    name="NotificationRuleFilter",
)
class NotificationRuleFilter:
    name: StringFilter | None = None
    rule_type: NotificationRuleTypeFilterGQL | None = None
    enabled: bool | None = None

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None

    def to_pydantic(self) -> NotificationRuleFilterDTO:
        return NotificationRuleFilterDTO(
            name=self.name.to_pydantic() if self.name is not None else None,
            rule_type=self.rule_type.to_pydantic() if self.rule_type is not None else None,
            enabled=self.enabled,
            AND=[f.to_pydantic() for f in self.AND] if self.AND is not None else None,
            OR=[f.to_pydantic() for f in self.OR] if self.OR is not None else None,
            NOT=[f.to_pydantic() for f in self.NOT] if self.NOT is not None else None,
        )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Order by specification for notification rules", added_version="24.09.0"
    ),
    model=NotificationRuleOrderDTO,
    name="NotificationRuleOrderBy",
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


@gql_pydantic_input(
    BackendAIGQLMeta(description="Input for webhook configuration", added_version="24.09.0"),
    model=WebhookSpecInputDTO,
    name="WebhookSpecInput",
)
class WebhookSpecInput:
    url: str

    def to_dataclass(self) -> WebhookSpec:
        return WebhookSpec(url=self.url)

    def to_pydantic(self) -> WebhookSpecInputDTO:
        return WebhookSpecInputDTO(url=self.url)


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for SMTP authentication credentials", added_version="24.09.0"
    ),
    model=SMTPAuthInputDTO,
    name="SMTPAuthInput",
)
class SMTPAuthInput:
    username: str | None = None
    password: str | None = None

    def to_dataclass(self) -> SMTPAuth:
        return SMTPAuth(username=self.username, password=self.password)

    def to_pydantic(self) -> SMTPAuthInputDTO:
        return SMTPAuthInputDTO(username=self.username, password=self.password)


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for SMTP server connection settings", added_version="24.09.0"
    ),
    model=SMTPConnectionInputDTO,
    name="SMTPConnectionInput",
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


@gql_pydantic_input(
    BackendAIGQLMeta(description="Input for email message settings", added_version="24.09.0"),
    model=EmailMessageInputDTO,
    name="EmailMessageInput",
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


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for email notification channel configuration", added_version="24.09.0"
    ),
    model=EmailSpecInputDTO,
    name="EmailSpecInput",
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


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for notification channel configuration. Exactly one of webhook or email must be set.",
        added_version="24.09.0",
    ),
    model=NotificationChannelSpecInputDTO,
    name="NotificationChannelSpecInput",
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

    def get_channel_type(self) -> NotificationChannelTypeDTO:
        """Get the channel type based on which field is set."""
        if self.webhook is not None and self.webhook is not UNSET:
            return NotificationChannelTypeDTO.WEBHOOK
        if self.email is not None and self.email is not UNSET:
            return NotificationChannelTypeDTO.EMAIL
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


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for creating a notification channel", added_version="24.09.0"
    ),
    model=CreateNotificationChannelInputDTO,
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
            channel_type=self.channel_type,
            spec=self.spec.to_dataclass(),
            enabled=self.enabled,
        )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for updating a notification channel", added_version="24.09.0"
    ),
    model=UpdateNotificationChannelInputDTO,
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


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for deleting a notification channel", added_version="24.09.0"
    ),
    model=DeleteNotificationChannelInputDTO,
)
class DeleteNotificationChannelInput:
    id: ID

    def to_pydantic(self) -> DeleteNotificationChannelInputDTO:
        return DeleteNotificationChannelInputDTO(
            id=uuid.UUID(str(self.id)),
        )


@gql_pydantic_input(
    BackendAIGQLMeta(description="Input for creating a notification rule", added_version="24.09.0"),
    model=CreateNotificationRuleInputDTO,
)
class CreateNotificationRuleInput:
    name: str
    description: str | None = None
    rule_type: NotificationRuleTypeGQL = strawberry.field()
    channel_id: ID
    message_template: str
    enabled: bool = True

    def to_pydantic(self) -> CreateNotificationRuleInputDTO:
        return CreateNotificationRuleInputDTO(
            name=self.name,
            description=self.description,
            rule_type=self.rule_type,
            channel_id=uuid.UUID(str(self.channel_id)),
            message_template=self.message_template,
            enabled=self.enabled,
        )


@gql_pydantic_input(
    BackendAIGQLMeta(description="Input for updating a notification rule", added_version="24.09.0"),
    model=UpdateNotificationRuleInputDTO,
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


@gql_pydantic_input(
    BackendAIGQLMeta(description="Input for deleting a notification rule", added_version="24.09.0"),
    model=DeleteNotificationRuleInputDTO,
)
class DeleteNotificationRuleInput:
    id: ID

    def to_pydantic(self) -> DeleteNotificationRuleInputDTO:
        return DeleteNotificationRuleInputDTO(
            id=uuid.UUID(str(self.id)),
        )


# Payload types for mutations


@gql_from_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0", description="Payload for create notification channel mutation."
    ),
)
class CreateNotificationChannelPayload(PydanticOutputMixin[CreateNotificationChannelPayloadDTO]):
    channel: NotificationChannel


@gql_from_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0", description="Payload for update notification channel mutation."
    ),
)
class UpdateNotificationChannelPayload(PydanticOutputMixin[UpdateNotificationChannelPayloadDTO]):
    channel: NotificationChannel


@gql_output_type(
    BackendAIGQLMeta(
        added_version="26.3.0", description="Payload for delete notification channel mutation."
    ),
    name="DeleteNotificationChannelPayload",
)
class DeleteNotificationChannelPayload:
    """Payload for notification channel deletion mutation."""

    id: ID = strawberry.field(description="ID of the deleted notification channel.")

    @classmethod
    def from_pydantic(cls, instance: DeleteNotificationChannelPayloadDTO) -> Self:
        return cls(id=ID(str(instance.id)))


@gql_from_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0", description="Payload for create notification rule mutation."
    ),
)
class CreateNotificationRulePayload(PydanticOutputMixin[CreateNotificationRulePayloadDTO]):
    rule: NotificationRule


@gql_from_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0", description="Payload for update notification rule mutation."
    ),
)
class UpdateNotificationRulePayload(PydanticOutputMixin[UpdateNotificationRulePayloadDTO]):
    rule: NotificationRule


@gql_output_type(
    BackendAIGQLMeta(
        added_version="26.3.0", description="Payload for delete notification rule mutation."
    ),
    name="DeleteNotificationRulePayload",
)
class DeleteNotificationRulePayload:
    """Payload for notification rule deletion mutation."""

    id: ID = strawberry.field(description="ID of the deleted notification rule.")

    @classmethod
    def from_pydantic(cls, instance: DeleteNotificationRulePayloadDTO) -> Self:
        return cls(id=ID(str(instance.id)))


# Validate mutations


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for validate notification channel mutation", added_version="24.09.0"
    ),
    model=ValidateNotificationChannelInputDTO,
)
class ValidateNotificationChannelInput:
    id: ID
    test_message: str

    def to_pydantic(self) -> ValidateNotificationChannelInputDTO:
        return ValidateNotificationChannelInputDTO(
            id=uuid.UUID(self.id),
            test_message=self.test_message,
        )


@gql_output_type(
    BackendAIGQLMeta(
        added_version="26.3.0", description="Payload for validate notification channel mutation."
    ),
    name="ValidateNotificationChannelPayload",
)
class ValidateNotificationChannelPayload:
    """Payload for notification channel validation mutation."""

    id: ID = strawberry.field(description="ID of the validated notification channel.")

    @classmethod
    def from_pydantic(cls, instance: ValidateNotificationChannelPayloadDTO) -> Self:
        return cls(id=ID(str(instance.channel_id)))


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for validate notification rule mutation", added_version="24.09.0"
    ),
    model=ValidateNotificationRuleInputDTO,
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


@gql_from_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0", description="Payload for validate notification rule mutation."
    ),
    name="ValidateNotificationRulePayload",
)
class ValidateNotificationRulePayload(PydanticOutputMixin[ValidateNotificationRulePayloadDTO]):
    """Payload for notification rule validation mutation."""

    message: str = strawberry.field(description="The rendered message from the template.")
