"""Notification domain adapter - Pydantic-in/Pydantic-out transport layer."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from ai.backend.common.api_handlers import Sentinel
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
from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.dto.manager.v2.notification.request import (
    CreateNotificationChannelInput,
    CreateNotificationRuleInput,
    DeleteNotificationChannelInput,
    DeleteNotificationRuleInput,
    NotificationChannelFilter,
    NotificationChannelOrder,
    NotificationChannelSpecInputDTO,
    NotificationRuleFilter,
    NotificationRuleOrder,
    SearchNotificationChannelsInput,
    SearchNotificationRulesInput,
    UpdateNotificationChannelInput,
    UpdateNotificationRuleInput,
    ValidateNotificationChannelInput,
    ValidateNotificationRuleInput,
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
    ValidateNotificationChannelPayload,
    ValidateNotificationRulePayload,
)
from ai.backend.common.dto.manager.v2.notification.types import (
    EmailMessageInfo,
    EmailSpecInfo,
    NotificationChannelOrderField,
    NotificationChannelTypeDTO,
    NotificationRuleOrderField,
    NotificationRuleTypeDTO,
    OrderDirection,
    SMTPAuthInfo,
    SMTPConnectionInfo,
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
    BatchQuerier,
    OffsetPagination,
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
    ValidateChannelAction,
    ValidateRuleAction,
)
from ai.backend.manager.types import OptionalState, TriState

from .base import BaseAdapter


def _spec_input_to_domain(spec: NotificationChannelSpecInputDTO) -> WebhookSpec | EmailSpec:
    """Convert NotificationChannelSpecInputDTO to domain WebhookSpec or EmailSpec."""
    if spec.webhook is not None:
        return WebhookSpec(url=spec.webhook.url)
    if spec.email is not None:
        return EmailSpec(
            smtp=SMTPConnection(
                host=spec.email.smtp.host,
                port=spec.email.smtp.port,
                use_tls=spec.email.smtp.use_tls,
                timeout=spec.email.smtp.timeout,
            ),
            message=EmailMessage(
                from_email=spec.email.message.from_email,
                to_emails=spec.email.message.to_emails,
                subject_template=spec.email.message.subject_template,
            ),
            auth=SMTPAuth(
                username=spec.email.auth.username,
                password=spec.email.auth.password,
            )
            if spec.email.auth is not None
            else None,
        )
    raise InvalidNotificationSpec("Exactly one of webhook or email must be set")


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

    async def batch_load_channels_by_ids(
        self, ids: Sequence[UUID]
    ) -> list[NotificationChannelNode | None]:
        """Batch load notification channels by ID for DataLoader use.

        Returns NotificationChannelNode DTOs in the same order as the input ids list.
        """
        if not ids:
            return []
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=len(ids)),
            conditions=[NotificationChannelConditions.by_ids(ids)],
        )
        action_result = await self._processors.notification.search_channels.wait_for_complete(
            SearchChannelsAction(querier=querier)
        )
        channel_map = {ch.id: self._channel_data_to_dto(ch) for ch in action_result.channels}
        return [channel_map.get(channel_id) for channel_id in ids]

    async def batch_load_rules_by_ids(
        self, ids: Sequence[UUID]
    ) -> list[NotificationRuleNode | None]:
        """Batch load notification rules by ID for DataLoader use.

        Returns NotificationRuleNode DTOs in the same order as the input ids list.
        """
        if not ids:
            return []
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=len(ids)),
            conditions=[NotificationRuleConditions.by_ids(ids)],
        )
        action_result = await self._processors.notification.search_rules.wait_for_complete(
            SearchRulesAction(querier=querier)
        )
        rule_map = {rule.id: self._rule_data_to_dto(rule) for rule in action_result.rules}
        return [rule_map.get(rule_id) for rule_id in ids]

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
                channel_type=NotificationChannelType(input.channel_type.value),
                spec=_spec_input_to_domain(input.spec),
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
                rule_type=NotificationRuleType(input.rule_type.value),
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

    async def validate_channel(
        self, input: ValidateNotificationChannelInput
    ) -> ValidateNotificationChannelPayload:
        """Validate a notification channel by sending a test message."""
        await self._processors.notification.validate_channel.wait_for_complete(
            ValidateChannelAction(channel_id=input.id, test_message=input.test_message)
        )
        return ValidateNotificationChannelPayload(id=input.id)

    async def validate_rule(
        self, input: ValidateNotificationRuleInput
    ) -> ValidateNotificationRulePayload:
        """Validate a notification rule by rendering its template with test data."""
        action_result = await self._processors.notification.validate_rule.wait_for_complete(
            ValidateRuleAction(rule_id=input.id, notification_data=input.notification_data or {})
        )
        return ValidateNotificationRulePayload(message=action_result.message)

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
                spec_info = WebhookSpecInfo(
                    channel_type=NotificationChannelTypeDTO.WEBHOOK,
                    url=data.spec.url,
                )
            case NotificationChannelType.EMAIL:
                if not isinstance(data.spec, EmailSpec):
                    raise InvalidNotificationSpec(
                        f"Expected EmailSpec for EMAIL channel, got {type(data.spec).__name__}"
                    )
                spec_info = EmailSpecInfo(
                    channel_type=NotificationChannelTypeDTO.EMAIL,
                    smtp=SMTPConnectionInfo(
                        host=data.spec.smtp.host,
                        port=data.spec.smtp.port,
                        use_tls=data.spec.smtp.use_tls,
                        timeout=data.spec.smtp.timeout,
                    ),
                    message=EmailMessageInfo(
                        from_email=data.spec.message.from_email,
                        to_emails=data.spec.message.to_emails,
                        subject_template=data.spec.message.subject_template,
                    ),
                    auth=(
                        SMTPAuthInfo(username=data.spec.auth.username)
                        if data.spec.auth is not None
                        else None
                    ),
                )
            case _:
                raise InvalidNotificationSpec(f"Unsupported channel type: {data.channel_type}")
        return NotificationChannelNode(
            id=data.id,
            name=data.name,
            description=data.description,
            channel_type=NotificationChannelTypeDTO(data.channel_type.value),
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
            rule_type=NotificationRuleTypeDTO(data.rule_type.value),
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
                OptionalState.update(_spec_input_to_domain(input.spec))
                if input.spec is not None
                else OptionalState.nop()
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
                conditions.append(
                    NotificationChannelConditions.by_channel_type_equals(
                        NotificationChannelType(ct.equals.value)
                    )
                )
            if ct.in_ is not None:
                conditions.append(
                    NotificationChannelConditions.by_channel_types([
                        NotificationChannelType(t.value) for t in ct.in_
                    ])
                )
            if ct.not_equals is not None:
                conditions.append(
                    NotificationChannelConditions.by_channel_type_not_equals(
                        NotificationChannelType(ct.not_equals.value)
                    )
                )
            if ct.not_in is not None:
                conditions.append(
                    NotificationChannelConditions.by_channel_type_not_in([
                        NotificationChannelType(t.value) for t in ct.not_in
                    ])
                )

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
                conditions.append(
                    NotificationRuleConditions.by_rule_type_equals(
                        NotificationRuleType(rt.equals.value)
                    )
                )
            if rt.in_ is not None:
                conditions.append(
                    NotificationRuleConditions.by_rule_types([
                        NotificationRuleType(t.value) for t in rt.in_
                    ])
                )
            if rt.not_equals is not None:
                conditions.append(
                    NotificationRuleConditions.by_rule_type_not_equals(
                        NotificationRuleType(rt.not_equals.value)
                    )
                )
            if rt.not_in is not None:
                conditions.append(
                    NotificationRuleConditions.by_rule_type_not_in([
                        NotificationRuleType(t.value) for t in rt.not_in
                    ])
                )

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
