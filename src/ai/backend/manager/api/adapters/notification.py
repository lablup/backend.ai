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
    NotificationChannelFilter,
    NotificationChannelOrder,
    NotificationRuleFilter,
    NotificationRuleOrder,
    SearchNotificationChannelsInput,
    SearchNotificationRulesInput,
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
    SearchNotificationChannelsPayload,
    SearchNotificationRulesPayload,
    UpdateNotificationChannelPayload,
    UpdateNotificationRulePayload,
)
from ai.backend.common.dto.manager.v2.notification.types import (
    EmailSpecInfo,
    NotificationChannelOrderField,
    NotificationRuleOrderField,
    OrderDirection,
    WebhookSpecInfo,
)
from ai.backend.manager.api.adapters.pagination import PaginationSpec
from ai.backend.manager.data.notification import NotificationChannelData, NotificationRuleData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.errors.notification import InvalidNotificationSpec
from ai.backend.manager.models.notification import NotificationChannelRow, NotificationRuleRow
from ai.backend.manager.models.notification.conditions import (
    NotificationChannelConditions,
    NotificationRuleConditions,
)
from ai.backend.manager.models.notification.orders import (
    NotificationChannelOrders,
    NotificationRuleOrders,
)
from ai.backend.manager.repositories.base import (
    QueryCondition,
    QueryOrder,
    Updater,
    combine_conditions_or,
    negate_conditions,
)
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
    SearchChannelsAction,
    SearchRulesAction,
    UpdateChannelAction,
    UpdateRuleAction,
)
from ai.backend.manager.types import OptionalState, TriState

from .base import BaseAdapter


def _channel_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=NotificationChannelOrders.created_at(ascending=False),
        backward_order=NotificationChannelOrders.created_at(ascending=True),
        forward_condition_factory=NotificationChannelConditions.by_cursor_forward,
        backward_condition_factory=NotificationChannelConditions.by_cursor_backward,
        tiebreaker_order=NotificationChannelRow.id.asc(),
    )


def _rule_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=NotificationRuleOrders.created_at(ascending=False),
        backward_order=NotificationRuleOrders.created_at(ascending=True),
        forward_condition_factory=NotificationRuleConditions.by_cursor_forward,
        backward_condition_factory=NotificationRuleConditions.by_cursor_backward,
        tiebreaker_order=NotificationRuleRow.id.asc(),
    )


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

    async def search_channels(
        self, input: SearchNotificationChannelsInput
    ) -> SearchNotificationChannelsPayload:
        """Search notification channels with filter, order, and pagination."""
        conditions = self._convert_channel_filter(input.filter) if input.filter else []
        orders = self._convert_channel_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_channel_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

        action_result = await self._processors.notification.search_channels.wait_for_complete(
            SearchChannelsAction(querier=querier)
        )

        return SearchNotificationChannelsPayload(
            items=[self._channel_data_to_dto(d) for d in action_result.channels],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def search_rules(
        self, input: SearchNotificationRulesInput
    ) -> SearchNotificationRulesPayload:
        """Search notification rules with filter, order, and pagination."""
        conditions = self._convert_rule_filter(input.filter) if input.filter else []
        orders = self._convert_rule_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_rule_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

        action_result = await self._processors.notification.search_rules.wait_for_complete(
            SearchRulesAction(querier=querier)
        )

        return SearchNotificationRulesPayload(
            items=[self._rule_data_to_dto(d) for d in action_result.rules],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

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
                    smtp_use_tls=data.spec.smtp.use_tls,
                    smtp_timeout=data.spec.smtp.timeout,
                    from_email=data.spec.message.from_email,
                    to_emails=data.spec.message.to_emails,
                    subject_template=data.spec.message.subject_template,
                    auth_username=data.spec.auth.username if data.spec.auth is not None else None,
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
                TriState[str].nop()
                if isinstance(input.description, Sentinel)
                else TriState[str].from_graphql(input.description)
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
                TriState[str].nop()
                if isinstance(input.description, Sentinel)
                else TriState[str].from_graphql(input.description)
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

    @staticmethod
    def _convert_channel_filter(f: NotificationChannelFilter) -> list[QueryCondition]:
        """Convert NotificationChannelFilter DTO to QueryCondition list."""
        conditions: list[QueryCondition] = []

        if f.name:
            cond = f.name.build_query_condition(
                contains_factory=NotificationChannelConditions.by_name_contains,
                equals_factory=NotificationChannelConditions.by_name_equals,
                starts_with_factory=NotificationChannelConditions.by_name_starts_with,
                ends_with_factory=NotificationChannelConditions.by_name_ends_with,
            )
            if cond:
                conditions.append(cond)

        if f.channel_type is not None:
            ct = f.channel_type
            if ct.equals is not None:
                conditions.append(NotificationChannelConditions.by_channel_type_equals(ct.equals))
            if ct.in_ is not None:
                conditions.append(NotificationChannelConditions.by_channel_types(list(ct.in_)))
            if ct.not_equals is not None:
                conditions.append(
                    NotificationChannelConditions.by_channel_type_not_equals(ct.not_equals)
                )
            if ct.not_in is not None:
                conditions.append(NotificationChannelConditions.by_channel_type_not_in(ct.not_in))

        if f.enabled is not None:
            conditions.append(NotificationChannelConditions.by_enabled(f.enabled))

        if f.AND:
            for sub in f.AND:
                conditions.extend(NotificationAdapter._convert_channel_filter(sub))

        if f.OR:
            or_conditions: list[QueryCondition] = []
            for sub in f.OR:
                or_conditions.extend(NotificationAdapter._convert_channel_filter(sub))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))

        if f.NOT:
            not_conditions: list[QueryCondition] = []
            for sub in f.NOT:
                not_conditions.extend(NotificationAdapter._convert_channel_filter(sub))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))

        return conditions

    @staticmethod
    def _convert_channel_orders(orders: list[NotificationChannelOrder]) -> list[QueryOrder]:
        """Convert NotificationChannelOrder DTO list to QueryOrder list."""
        result: list[QueryOrder] = []
        for o in orders:
            ascending = o.direction == OrderDirection.ASC
            match o.field:
                case NotificationChannelOrderField.NAME:
                    result.append(NotificationChannelOrders.name(ascending))
                case NotificationChannelOrderField.CREATED_AT:
                    result.append(NotificationChannelOrders.created_at(ascending))
                case NotificationChannelOrderField.UPDATED_AT:
                    result.append(NotificationChannelOrders.updated_at(ascending))
        return result

    @staticmethod
    def _convert_rule_filter(f: NotificationRuleFilter) -> list[QueryCondition]:
        """Convert NotificationRuleFilter DTO to QueryCondition list."""
        conditions: list[QueryCondition] = []

        if f.name:
            cond = f.name.build_query_condition(
                contains_factory=NotificationRuleConditions.by_name_contains,
                equals_factory=NotificationRuleConditions.by_name_equals,
                starts_with_factory=NotificationRuleConditions.by_name_starts_with,
                ends_with_factory=NotificationRuleConditions.by_name_ends_with,
            )
            if cond:
                conditions.append(cond)

        if f.rule_type is not None:
            rt = f.rule_type
            if rt.equals is not None:
                conditions.append(NotificationRuleConditions.by_rule_type_equals(rt.equals))
            if rt.in_ is not None:
                conditions.append(NotificationRuleConditions.by_rule_types(list(rt.in_)))
            if rt.not_equals is not None:
                conditions.append(NotificationRuleConditions.by_rule_type_not_equals(rt.not_equals))
            if rt.not_in is not None:
                conditions.append(NotificationRuleConditions.by_rule_type_not_in(rt.not_in))

        if f.enabled is not None:
            conditions.append(NotificationRuleConditions.by_enabled(f.enabled))

        if f.AND:
            for sub in f.AND:
                conditions.extend(NotificationAdapter._convert_rule_filter(sub))

        if f.OR:
            or_conditions: list[QueryCondition] = []
            for sub in f.OR:
                or_conditions.extend(NotificationAdapter._convert_rule_filter(sub))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))

        if f.NOT:
            not_conditions: list[QueryCondition] = []
            for sub in f.NOT:
                not_conditions.extend(NotificationAdapter._convert_rule_filter(sub))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))

        return conditions

    @staticmethod
    def _convert_rule_orders(orders: list[NotificationRuleOrder]) -> list[QueryOrder]:
        """Convert NotificationRuleOrder DTO list to QueryOrder list."""
        result: list[QueryOrder] = []
        for o in orders:
            ascending = o.direction == OrderDirection.ASC
            match o.field:
                case NotificationRuleOrderField.NAME:
                    result.append(NotificationRuleOrders.name(ascending))
                case NotificationRuleOrderField.CREATED_AT:
                    result.append(NotificationRuleOrders.created_at(ascending))
                case NotificationRuleOrderField.UPDATED_AT:
                    result.append(NotificationRuleOrders.updated_at(ascending))
        return result
