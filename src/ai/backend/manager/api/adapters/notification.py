"""Notification domain adapter - Pydantic-in/Pydantic-out transport layer."""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.api_handlers import Sentinel
from ai.backend.common.data.notification import NotificationChannelType, WebhookSpec
from ai.backend.common.data.notification.types import EmailSpec
from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.dto.manager.v2.notification.request import (
    CreateNotificationChannelInput,
    CreateNotificationRuleInput,
    DeleteNotificationChannelInput,
    DeleteNotificationRuleInput,
    UpdateNotificationChannelInput,
    UpdateNotificationRuleInput,
)
from ai.backend.common.dto.manager.v2.notification.response import (
    CreateNotificationChannelPayload,
    CreateNotificationRulePayload,
    DeleteNotificationChannelPayload,
    DeleteNotificationRulePayload,
    GetNotificationChannelPayload,
    GetNotificationRulePayload,
    NotificationChannelNode,
    NotificationRuleNode,
    UpdateNotificationChannelPayload,
    UpdateNotificationRulePayload,
)
from ai.backend.common.dto.manager.v2.notification.types import EmailSpecInfo, WebhookSpecInfo
from ai.backend.manager.data.notification import NotificationChannelData, NotificationRuleData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.errors.notification import InvalidNotificationSpec
from ai.backend.manager.models.notification import NotificationChannelRow, NotificationRuleRow
from ai.backend.manager.repositories.base import Updater
from ai.backend.manager.repositories.base.rbac.entity_creator import RBACEntityCreator
from ai.backend.manager.repositories.notification.creators import (
    NotificationChannelCreatorSpec,
    NotificationRuleCreatorSpec,
)
from ai.backend.manager.repositories.notification.updaters import (
    NotificationChannelUpdaterSpec,
    NotificationRuleUpdaterSpec,
)
from ai.backend.manager.services.notification.actions import (
    CreateChannelAction,
    CreateRuleAction,
    DeleteChannelAction,
    DeleteRuleAction,
    GetChannelAction,
    GetRuleAction,
    UpdateChannelAction,
    UpdateRuleAction,
)
from ai.backend.manager.types import OptionalState

from .base import BaseAdapter


class NotificationAdapter(BaseAdapter):
    """Adapter for notification domain operations (channel + rule)."""

    # ------------------------------------------------------------------ channels

    async def create_channel(
        self,
        input: CreateNotificationChannelInput,
        created_by: UUID,
    ) -> CreateNotificationChannelPayload:
        """Create a new notification channel."""
        creator: RBACEntityCreator[NotificationChannelRow] = RBACEntityCreator(
            spec=NotificationChannelCreatorSpec(
                name=input.name,
                description=input.description,
                channel_type=input.channel_type,
                spec=input.spec,
                enabled=input.enabled,
                created_by=created_by,
            ),
            element_type=RBACElementType.NOTIFICATION_CHANNEL,
            scope_ref=RBACElementRef(RBACElementType.USER, str(created_by)),
        )

        action_result = await self._processors.notification.create_channel.wait_for_complete(
            CreateChannelAction(creator=creator)
        )

        return CreateNotificationChannelPayload(
            channel=self._channel_data_to_dto(action_result.channel_data)
        )

    async def get_channel(self, channel_id: UUID) -> GetNotificationChannelPayload:
        """Get a notification channel by ID."""
        action_result = await self._processors.notification.get_channel.wait_for_complete(
            GetChannelAction(channel_id=channel_id)
        )

        return GetNotificationChannelPayload(
            item=self._channel_data_to_dto(action_result.channel_data)
        )

    async def update_channel(
        self,
        channel_id: UUID,
        input: UpdateNotificationChannelInput,
    ) -> UpdateNotificationChannelPayload:
        """Update an existing notification channel."""
        updater: Updater[NotificationChannelRow] = Updater(
            spec=self._build_channel_updater_spec(input),
            pk_value=channel_id,
        )

        action_result = await self._processors.notification.update_channel.wait_for_complete(
            UpdateChannelAction(updater=updater)
        )

        return UpdateNotificationChannelPayload(
            channel=self._channel_data_to_dto(action_result.channel_data)
        )

    async def delete_channel(
        self, input: DeleteNotificationChannelInput
    ) -> DeleteNotificationChannelPayload:
        """Delete a notification channel."""
        await self._processors.notification.delete_channel.wait_for_complete(
            DeleteChannelAction(channel_id=input.id)
        )

        return DeleteNotificationChannelPayload(id=input.id)

    # ------------------------------------------------------------------ rules

    async def create_rule(
        self,
        input: CreateNotificationRuleInput,
        created_by: UUID,
    ) -> CreateNotificationRulePayload:
        """Create a new notification rule."""
        creator: RBACEntityCreator[NotificationRuleRow] = RBACEntityCreator(
            spec=NotificationRuleCreatorSpec(
                name=input.name,
                description=input.description,
                rule_type=input.rule_type,
                channel_id=input.channel_id,
                message_template=input.message_template,
                enabled=input.enabled,
                created_by=created_by,
            ),
            element_type=RBACElementType.NOTIFICATION_RULE,
            scope_ref=RBACElementRef(RBACElementType.NOTIFICATION_CHANNEL, str(input.channel_id)),
        )

        action_result = await self._processors.notification.create_rule.wait_for_complete(
            CreateRuleAction(creator=creator)
        )

        return CreateNotificationRulePayload(rule=self._rule_data_to_dto(action_result.rule_data))

    async def get_rule(self, rule_id: UUID) -> GetNotificationRulePayload:
        """Get a notification rule by ID."""
        action_result = await self._processors.notification.get_rule.wait_for_complete(
            GetRuleAction(rule_id=rule_id)
        )

        return GetNotificationRulePayload(item=self._rule_data_to_dto(action_result.rule_data))

    async def update_rule(
        self,
        rule_id: UUID,
        input: UpdateNotificationRuleInput,
    ) -> UpdateNotificationRulePayload:
        """Update an existing notification rule."""
        updater: Updater[NotificationRuleRow] = Updater(
            spec=self._build_rule_updater_spec(input),
            pk_value=rule_id,
        )

        action_result = await self._processors.notification.update_rule.wait_for_complete(
            UpdateRuleAction(updater=updater)
        )

        return UpdateNotificationRulePayload(rule=self._rule_data_to_dto(action_result.rule_data))

    async def delete_rule(
        self, input: DeleteNotificationRuleInput
    ) -> DeleteNotificationRulePayload:
        """Delete a notification rule."""
        await self._processors.notification.delete_rule.wait_for_complete(
            DeleteRuleAction(rule_id=input.id)
        )

        return DeleteNotificationRulePayload(id=input.id)

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def _channel_data_to_dto(data: NotificationChannelData) -> NotificationChannelNode:
        """Convert NotificationChannelData to NotificationChannelNode DTO."""
        spec_info: WebhookSpecInfo | EmailSpecInfo
        match data.channel_type:
            case NotificationChannelType.WEBHOOK:
                if not isinstance(data.spec, WebhookSpec):
                    raise InvalidNotificationSpec(
                        f"Expected WebhookSpec for WEBHOOK channel, got {type(data.spec).__name__}"
                    )
                spec_info = WebhookSpecInfo(url=data.spec.url)
            case NotificationChannelType.EMAIL:
                if not isinstance(data.spec, EmailSpec):
                    raise InvalidNotificationSpec(
                        f"Expected EmailSpec for EMAIL channel, got {type(data.spec).__name__}"
                    )
                spec_info = EmailSpecInfo(
                    smtp_host=data.spec.smtp.host,
                    smtp_port=data.spec.smtp.port,
                    from_email=data.spec.message.from_email,
                    to_emails=data.spec.message.to_emails,
                )
            case _:
                raise InvalidNotificationSpec(f"Unsupported channel type: {data.channel_type}")
        return NotificationChannelNode(
            id=data.id,
            name=data.name,
            description=data.description,
            channel_type=data.channel_type,
            spec=spec_info,
            enabled=data.enabled,
            created_at=data.created_at,
            created_by=data.created_by,
            updated_at=data.updated_at,
        )

    @classmethod
    def _rule_data_to_dto(cls, data: NotificationRuleData) -> NotificationRuleNode:
        """Convert NotificationRuleData to NotificationRuleNode DTO."""
        return NotificationRuleNode(
            id=data.id,
            name=data.name,
            description=data.description,
            rule_type=data.rule_type,
            channel=cls._channel_data_to_dto(data.channel),
            message_template=data.message_template,
            enabled=data.enabled,
            created_at=data.created_at,
            created_by=data.created_by,
            updated_at=data.updated_at,
        )

    @staticmethod
    def _build_channel_updater_spec(
        input: UpdateNotificationChannelInput,
    ) -> NotificationChannelUpdaterSpec:
        return NotificationChannelUpdaterSpec(
            name=(
                OptionalState.update(input.name) if input.name is not None else OptionalState.nop()
            ),
            description=(
                OptionalState[str | None].nop()
                if isinstance(input.description, Sentinel)
                else OptionalState[str | None].update(input.description)
            ),
            spec=(
                OptionalState.update(input.spec) if input.spec is not None else OptionalState.nop()
            ),
            enabled=(
                OptionalState.update(input.enabled)
                if input.enabled is not None
                else OptionalState.nop()
            ),
        )

    @staticmethod
    def _build_rule_updater_spec(
        input: UpdateNotificationRuleInput,
    ) -> NotificationRuleUpdaterSpec:
        return NotificationRuleUpdaterSpec(
            name=(
                OptionalState.update(input.name) if input.name is not None else OptionalState.nop()
            ),
            description=(
                OptionalState[str | None].nop()
                if isinstance(input.description, Sentinel)
                else OptionalState[str | None].update(input.description)
            ),
            message_template=(
                OptionalState.update(input.message_template)
                if input.message_template is not None
                else OptionalState.nop()
            ),
            enabled=(
                OptionalState.update(input.enabled)
                if input.enabled is not None
                else OptionalState.nop()
            ),
        )
