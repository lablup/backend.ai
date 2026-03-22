"""GraphQL types, filters, and inputs for notification system."""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from typing import Self

import strawberry
from strawberry import ID, UNSET, Info
from strawberry.relay import NodeID

# NOTE: NotificationChannelSpecGQL uses @gql_pydantic_interface so Strawberry
# dispatches from_pydantic() to the concrete implementor (WebhookSpecGQL /
# EmailSpecGQL) based on the runtime DTO type.  No _pydantic_extra needed in
# NotificationChannel.
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
    EmailMessageInfo,
    EmailSpecInfo,
    NotificationChannelSpecInfo,
    NotificationChannelTypeDTO,
    NotificationRuleTypeDTO,
    SMTPAuthInfo,
    SMTPConnectionInfo,
    WebhookSpecInfo,
)
from ai.backend.common.exception import InvalidNotificationChannelSpec
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_interface,
    gql_pydantic_type,
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
@gql_pydantic_interface(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Interface for notification channel specifications.",
    ),
    model=NotificationChannelSpecInfo,
    name="NotificationChannelSpec",
)
class NotificationChannelSpecGQL:
    channel_type: NotificationChannelTypeGQL


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0", description="Specification for webhook notification channel."
    ),
    model=WebhookSpecInfo,
    name="WebhookSpec",
)
class WebhookSpecGQL(NotificationChannelSpecGQL):
    channel_type: NotificationChannelTypeGQL
    url: str


@gql_pydantic_type(
    BackendAIGQLMeta(added_version="26.3.0", description="SMTP authentication credentials."),
    model=SMTPAuthInfo,
    name="SMTPAuth",
)
class SMTPAuthGQL:
    username: str | None


@gql_pydantic_type(
    BackendAIGQLMeta(added_version="26.3.0", description="SMTP server connection settings."),
    model=SMTPConnectionInfo,
    name="SMTPConnection",
)
class SMTPConnectionGQL:
    host: str
    port: int
    use_tls: bool
    timeout: int


@gql_pydantic_type(
    BackendAIGQLMeta(added_version="26.3.0", description="Email message settings."),
    model=EmailMessageInfo,
    name="EmailMessage",
)
class EmailMessageGQL:
    from_email: str
    to_emails: list[str]
    subject_template: str | None


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0", description="Specification for email notification channel."
    ),
    model=EmailSpecInfo,
    name="EmailSpec",
)
class EmailSpecGQL(NotificationChannelSpecGQL):
    channel_type: NotificationChannelTypeGQL
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
    name="NotificationChannelTypeFilter",
)
class NotificationChannelTypeFilterGQL(PydanticInputMixin[NotificationChannelTypeFilterDTO]):
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


@gql_pydantic_input(
    BackendAIGQLMeta(description="Filter for notification channels", added_version="24.09.0"),
    name="NotificationChannelFilter",
)
class NotificationChannelFilter(PydanticInputMixin[NotificationChannelFilterDTO]):
    name: StringFilter | None = None
    channel_type: NotificationChannelTypeFilterGQL | None = None
    enabled: bool | None = None

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Order by specification for notification channels", added_version="24.09.0"
    ),
    name="NotificationChannelOrderBy",
)
class NotificationChannelOrderBy(PydanticInputMixin[NotificationChannelOrderDTO]):
    field: NotificationChannelOrderField
    direction: OrderDirection = OrderDirection.ASC


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
    name="NotificationRuleTypeFilter",
)
class NotificationRuleTypeFilterGQL(PydanticInputMixin[NotificationRuleTypeFilterDTO]):
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


@gql_pydantic_input(
    BackendAIGQLMeta(description="Filter for notification rules", added_version="24.09.0"),
    name="NotificationRuleFilter",
)
class NotificationRuleFilter(PydanticInputMixin[NotificationRuleFilterDTO]):
    name: StringFilter | None = None
    rule_type: NotificationRuleTypeFilterGQL | None = None
    enabled: bool | None = None

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Order by specification for notification rules", added_version="24.09.0"
    ),
    name="NotificationRuleOrderBy",
)
class NotificationRuleOrderBy(PydanticInputMixin[NotificationRuleOrderDTO]):
    field: NotificationRuleOrderField
    direction: OrderDirection = OrderDirection.ASC


# Input types for mutations


@gql_pydantic_input(
    BackendAIGQLMeta(description="Input for webhook configuration", added_version="24.09.0"),
    name="WebhookSpecInput",
)
class WebhookSpecInput(PydanticInputMixin[WebhookSpecInputDTO]):
    url: str

    def to_dataclass(self) -> WebhookSpec:
        return WebhookSpec(url=self.url)


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for SMTP authentication credentials", added_version="24.09.0"
    ),
    name="SMTPAuthInput",
)
class SMTPAuthInput(PydanticInputMixin[SMTPAuthInputDTO]):
    username: str | None = None
    password: str | None = None

    def to_dataclass(self) -> SMTPAuth:
        return SMTPAuth(username=self.username, password=self.password)


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for SMTP server connection settings", added_version="24.09.0"
    ),
    name="SMTPConnectionInput",
)
class SMTPConnectionInput(PydanticInputMixin[SMTPConnectionInputDTO]):
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


@gql_pydantic_input(
    BackendAIGQLMeta(description="Input for email message settings", added_version="24.09.0"),
    name="EmailMessageInput",
)
class EmailMessageInput(PydanticInputMixin[EmailMessageInputDTO]):
    from_email: str
    to_emails: list[str]
    subject_template: str | None = None

    def to_dataclass(self) -> EmailMessage:
        return EmailMessage(
            from_email=self.from_email,
            to_emails=self.to_emails,
            subject_template=self.subject_template,
        )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for email notification channel configuration", added_version="24.09.0"
    ),
    name="EmailSpecInput",
)
class EmailSpecInput(PydanticInputMixin[EmailSpecInputDTO]):
    smtp: SMTPConnectionInput
    message: EmailMessageInput
    auth: SMTPAuthInput | None = None

    def to_dataclass(self) -> EmailSpec:
        return EmailSpec(
            smtp=self.smtp.to_dataclass(),
            message=self.message.to_dataclass(),
            auth=self.auth.to_dataclass() if self.auth else None,
        )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for notification channel configuration. Exactly one of webhook or email must be set.",
        added_version="24.09.0",
    ),
    name="NotificationChannelSpecInput",
    one_of=True,
)
class NotificationChannelSpecInput(PydanticInputMixin[NotificationChannelSpecInputDTO]):
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


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for creating a notification channel", added_version="24.09.0"
    ),
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
)
class DeleteNotificationChannelInput(PydanticInputMixin[DeleteNotificationChannelInputDTO]):
    id: ID


@gql_pydantic_input(
    BackendAIGQLMeta(description="Input for creating a notification rule", added_version="24.09.0"),
)
class CreateNotificationRuleInput(PydanticInputMixin[CreateNotificationRuleInputDTO]):
    name: str
    description: str | None = None
    rule_type: NotificationRuleTypeGQL = strawberry.field()
    channel_id: ID
    message_template: str
    enabled: bool = True


@gql_pydantic_input(
    BackendAIGQLMeta(description="Input for updating a notification rule", added_version="24.09.0"),
)
class UpdateNotificationRuleInput(PydanticInputMixin[UpdateNotificationRuleInputDTO]):
    id: ID
    name: str | None = UNSET
    description: str | None = UNSET
    message_template: str | None = UNSET
    enabled: bool | None = UNSET


@gql_pydantic_input(
    BackendAIGQLMeta(description="Input for deleting a notification rule", added_version="24.09.0"),
)
class DeleteNotificationRuleInput(PydanticInputMixin[DeleteNotificationRuleInputDTO]):
    id: ID


# Payload types for mutations


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0", description="Payload for create notification channel mutation."
    ),
    model=CreateNotificationChannelPayloadDTO,
)
class CreateNotificationChannelPayload(PydanticOutputMixin[CreateNotificationChannelPayloadDTO]):
    channel: NotificationChannel


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0", description="Payload for update notification channel mutation."
    ),
    model=UpdateNotificationChannelPayloadDTO,
)
class UpdateNotificationChannelPayload(PydanticOutputMixin[UpdateNotificationChannelPayloadDTO]):
    channel: NotificationChannel


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0", description="Payload for delete notification channel mutation."
    ),
    model=DeleteNotificationChannelPayloadDTO,
    fields=["id"],
)
class DeleteNotificationChannelPayload(PydanticOutputMixin[DeleteNotificationChannelPayloadDTO]):
    id: ID = strawberry.field(description="ID of the deleted notification channel.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0", description="Payload for create notification rule mutation."
    ),
    model=CreateNotificationRulePayloadDTO,
)
class CreateNotificationRulePayload(PydanticOutputMixin[CreateNotificationRulePayloadDTO]):
    rule: NotificationRule


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0", description="Payload for update notification rule mutation."
    ),
    model=UpdateNotificationRulePayloadDTO,
)
class UpdateNotificationRulePayload(PydanticOutputMixin[UpdateNotificationRulePayloadDTO]):
    rule: NotificationRule


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0", description="Payload for delete notification rule mutation."
    ),
    model=DeleteNotificationRulePayloadDTO,
    fields=["id"],
)
class DeleteNotificationRulePayload(PydanticOutputMixin[DeleteNotificationRulePayloadDTO]):
    id: ID = strawberry.field(description="ID of the deleted notification rule.")


# Validate mutations


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for validate notification channel mutation", added_version="24.09.0"
    ),
)
class ValidateNotificationChannelInput(PydanticInputMixin[ValidateNotificationChannelInputDTO]):
    id: ID
    test_message: str


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0", description="Payload for validate notification channel mutation."
    ),
    model=ValidateNotificationChannelPayloadDTO,
    fields=["id"],
)
class ValidateNotificationChannelPayload(
    PydanticOutputMixin[ValidateNotificationChannelPayloadDTO]
):
    id: ID = strawberry.field(description="ID of the validated notification channel.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for validate notification rule mutation", added_version="24.09.0"
    ),
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


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0", description="Payload for validate notification rule mutation."
    ),
    model=ValidateNotificationRulePayloadDTO,
    all_fields=True,
    name="ValidateNotificationRulePayload",
)
class ValidateNotificationRulePayload(PydanticOutputMixin[ValidateNotificationRulePayloadDTO]):
    pass
