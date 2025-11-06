"""GraphQL types and mutations for notification system."""

from __future__ import annotations

import uuid
from enum import StrEnum
from typing import Optional, Self

import strawberry
from strawberry import ID, UNSET, Info
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.common.contexts.user import current_user
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter, to_global_id
from ai.backend.manager.data.notification import (
    NotificationChannelCreator,
    NotificationChannelData,
    NotificationChannelModifier,
    NotificationChannelType,
    NotificationRuleCreator,
    NotificationRuleData,
    NotificationRuleModifier,
    NotificationRuleType,
    WebhookConfig,
)
from ai.backend.manager.repositories.base import (
    CursorBackwardPagination,
    CursorForwardPagination,
    OffsetPagination,
    Querier,
    QueryCondition,
    QueryOrder,
    QueryPagination,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.repositories.notification.options import (
    NotificationChannelConditions,
    NotificationChannelOrders,
    NotificationRuleConditions,
    NotificationRuleOrders,
)
from ai.backend.manager.services.notification.actions import (
    CreateChannelAction,
    CreateRuleAction,
    DeleteChannelAction,
    DeleteRuleAction,
    GetChannelAction,
    GetRuleAction,
    ListChannelsAction,
    ListRulesAction,
    UpdateChannelAction,
    UpdateRuleAction,
)
from ai.backend.manager.types import OptionalState

from .types import StrawberryGQLContext

# GraphQL enum types


@strawberry.enum(description="Notification channel types")
class NotificationChannelTypeGQL(StrEnum):
    WEBHOOK = "webhook"

    @classmethod
    def from_internal(cls, internal_type: NotificationChannelType) -> NotificationChannelTypeGQL:
        """Convert internal NotificationChannelType to GraphQL enum."""
        match internal_type:
            case NotificationChannelType.WEBHOOK:
                return cls.WEBHOOK
            case _:
                raise ValueError(f"Unknown NotificationChannelType: {internal_type}")

    def to_internal(self) -> NotificationChannelType:
        """Convert GraphQL enum to internal NotificationChannelType."""
        match self:
            case NotificationChannelTypeGQL.WEBHOOK:
                return NotificationChannelType.WEBHOOK
            case _:
                raise ValueError(f"Unknown NotificationChannelTypeGQL: {self}")


@strawberry.enum(description="Notification rule types")
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
            case _:
                raise ValueError(f"Unknown NotificationRuleType: {internal_type}")

    def to_internal(self) -> NotificationRuleType:
        """Convert GraphQL enum to internal NotificationRuleType."""
        match self:
            case NotificationRuleTypeGQL.SESSION_STARTED:
                return NotificationRuleType.SESSION_STARTED
            case NotificationRuleTypeGQL.SESSION_TERMINATED:
                return NotificationRuleType.SESSION_TERMINATED
            case NotificationRuleTypeGQL.ARTIFACT_DOWNLOAD_COMPLETED:
                return NotificationRuleType.ARTIFACT_DOWNLOAD_COMPLETED
            case _:
                raise ValueError(f"Unknown NotificationRuleTypeGQL: {self}")


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

    @classmethod
    def from_dataclass(cls, data: NotificationChannelData) -> Self:
        return cls(
            id=ID(str(data.id)),
            name=data.name,
            description=data.description,
            channel_type=NotificationChannelTypeGQL.from_internal(data.channel_type),
            config=WebhookConfigGQL.from_dataclass(data.config),
            enabled=data.enabled,
        )


NotificationChannelEdge = Edge[NotificationChannel]


@strawberry.type(description="Notification channel connection")
class NotificationChannelConnection(Connection[NotificationChannel]):
    @strawberry.field
    def count(self) -> int:
        return len(self.edges)


@strawberry.type(description="Notification rule")
class NotificationRule(Node):
    id: NodeID[str]
    name: str
    description: Optional[str]
    rule_type: NotificationRuleTypeGQL
    channel: NotificationChannel
    message_template: str
    enabled: bool

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
        )


NotificationRuleEdge = Edge[NotificationRule]


@strawberry.type(description="Notification rule connection")
class NotificationRuleConnection(Connection[NotificationRule]):
    @strawberry.field
    def count(self) -> int:
        return len(self.edges)


# Filter and OrderBy types


@strawberry.enum
class NotificationChannelOrderField(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


@strawberry.input(description="Filter for notification channels")
class NotificationChannelFilter:
    name: Optional[StringFilter] = None
    channel_type: Optional[list[NotificationChannelTypeGQL]] = None
    enabled: Optional[bool] = None

    AND: Optional[list[NotificationChannelFilter]] = None
    OR: Optional[list[NotificationChannelFilter]] = None
    NOT: Optional[list[NotificationChannelFilter]] = None

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
class NotificationChannelOrderBy:
    field: NotificationChannelOrderField
    direction: OrderDirection = OrderDirection.ASC


@strawberry.enum
class NotificationRuleOrderField(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


@strawberry.input(description="Filter for notification rules")
class NotificationRuleFilter:
    name: Optional[StringFilter] = None
    rule_type: Optional[list[NotificationRuleTypeGQL]] = None
    enabled: Optional[bool] = None

    AND: Optional[list[NotificationRuleFilter]] = None
    OR: Optional[list[NotificationRuleFilter]] = None
    NOT: Optional[list[NotificationRuleFilter]] = None

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
class NotificationRuleOrderBy:
    field: NotificationRuleOrderField
    direction: OrderDirection = OrderDirection.ASC


# Helper functions for converting GraphQL filters to repository queriers


def _build_channel_querier(
    filter: Optional[NotificationChannelFilter] = None,
    order_by: Optional[NotificationChannelOrderBy] = None,
    first: Optional[int] = None,
    after: Optional[str] = None,
    last: Optional[int] = None,
    before: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Querier:
    """Build Querier from GraphQL filter, order_by, and pagination."""
    conditions: list[QueryCondition] = []
    orders: list[QueryOrder] = []
    pagination: Optional[QueryPagination] = None

    if filter:
        conditions.extend(filter.build_conditions())

    if order_by:
        orders.append(_build_channel_order(order_by))

    # Validate and build pagination
    # Count how many pagination modes are being used
    pagination_modes = sum([
        first is not None,
        last is not None,
        limit is not None,
    ])

    if pagination_modes > 1:
        raise ValueError(
            "Only one pagination mode allowed: (first/after) OR (last/before) OR (limit/offset)"
        )

    # Build appropriate pagination based on parameters
    if first is not None:
        if first <= 0:
            raise ValueError(f"first must be positive, got {first}")
        if after is None:
            raise ValueError("after cursor is required when using first")
        pagination = CursorForwardPagination(first=first, after=after)
    elif last is not None:
        if last <= 0:
            raise ValueError(f"last must be positive, got {last}")
        if before is None:
            raise ValueError("before cursor is required when using last")
        pagination = CursorBackwardPagination(last=last, before=before)
    elif limit is not None:
        if limit <= 0:
            raise ValueError(f"limit must be positive, got {limit}")
        if offset is not None and offset < 0:
            raise ValueError(f"offset must be non-negative, got {offset}")
        pagination = OffsetPagination(limit=limit, offset=offset or 0)

    return Querier(conditions=conditions, orders=orders, pagination=pagination)


def _build_channel_order(order_by: NotificationChannelOrderBy) -> QueryOrder:
    """Build query order from NotificationChannelOrderBy."""
    ascending = order_by.direction == OrderDirection.ASC
    match order_by.field:
        case NotificationChannelOrderField.NAME:
            return NotificationChannelOrders.name(ascending)
        case NotificationChannelOrderField.CREATED_AT:
            return NotificationChannelOrders.created_at(ascending)
        case NotificationChannelOrderField.UPDATED_AT:
            return NotificationChannelOrders.updated_at(ascending)
        case _:
            return NotificationChannelOrders.name(ascending)


def _build_rule_querier(
    filter: Optional[NotificationRuleFilter] = None,
    order_by: Optional[NotificationRuleOrderBy] = None,
    first: Optional[int] = None,
    after: Optional[str] = None,
    last: Optional[int] = None,
    before: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Querier:
    """Build Querier from GraphQL filter, order_by, and pagination."""
    conditions: list[QueryCondition] = []
    orders: list[QueryOrder] = []
    pagination: Optional[QueryPagination] = None

    if filter:
        conditions.extend(filter.build_conditions())

    if order_by:
        orders.append(_build_rule_order(order_by))

    # Validate and build pagination
    # Count how many pagination modes are being used
    pagination_modes = sum([
        first is not None,
        last is not None,
        limit is not None,
    ])

    if pagination_modes > 1:
        raise ValueError(
            "Only one pagination mode allowed: (first/after) OR (last/before) OR (limit/offset)"
        )

    # Build appropriate pagination based on parameters
    if first is not None:
        if first <= 0:
            raise ValueError(f"first must be positive, got {first}")
        if after is None:
            raise ValueError("after cursor is required when using first")
        pagination = CursorForwardPagination(first=first, after=after)
    elif last is not None:
        if last <= 0:
            raise ValueError(f"last must be positive, got {last}")
        if before is None:
            raise ValueError("before cursor is required when using last")
        pagination = CursorBackwardPagination(last=last, before=before)
    elif limit is not None:
        if limit <= 0:
            raise ValueError(f"limit must be positive, got {limit}")
        if offset is not None and offset < 0:
            raise ValueError(f"offset must be non-negative, got {offset}")
        pagination = OffsetPagination(limit=limit, offset=offset or 0)

    return Querier(conditions=conditions, orders=orders, pagination=pagination)


def _build_rule_order(order_by: NotificationRuleOrderBy) -> QueryOrder:
    """Build query order from NotificationRuleOrderBy."""
    ascending = order_by.direction == OrderDirection.ASC
    match order_by.field:
        case NotificationRuleOrderField.NAME:
            return NotificationRuleOrders.name(ascending)
        case NotificationRuleOrderField.CREATED_AT:
            return NotificationRuleOrders.created_at(ascending)
        case NotificationRuleOrderField.UPDATED_AT:
            return NotificationRuleOrders.updated_at(ascending)
        case _:
            return NotificationRuleOrders.name(ascending)


# Query fields


@strawberry.field(description="Get a notification channel by ID")
async def notification_channel(
    id: ID, info: Info[StrawberryGQLContext]
) -> Optional[NotificationChannel]:
    processors = info.context.processors
    action_result = await processors.notification.get_channel.wait_for_complete(
        GetChannelAction(channel_id=uuid.UUID(id))
    )
    return NotificationChannel.from_dataclass(action_result.channel_data)


@strawberry.field(description="List notification channels")
async def notification_channels(
    info: Info[StrawberryGQLContext],
    filter: Optional[NotificationChannelFilter] = None,
    order_by: Optional[NotificationChannelOrderBy] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> NotificationChannelConnection:
    processors = info.context.processors

    # Build querier from filter, order_by, and pagination
    querier = _build_channel_querier(
        filter=filter,
        order_by=order_by,
        first=first,
        after=after,
        last=last,
        before=before,
        limit=limit,
        offset=offset,
    )

    action_result = await processors.notification.list_channels.wait_for_complete(
        ListChannelsAction(querier=querier)
    )

    nodes = [NotificationChannel.from_dataclass(data) for data in action_result.channels]

    edges = [
        NotificationChannelEdge(node=node, cursor=to_global_id(NotificationChannel, node.id))
        for node in nodes
    ]

    return NotificationChannelConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
    )


@strawberry.field(description="Get a notification rule by ID")
async def notification_rule(id: ID, info: Info[StrawberryGQLContext]) -> Optional[NotificationRule]:
    processors = info.context.processors
    action_result = await processors.notification.get_rule.wait_for_complete(
        GetRuleAction(rule_id=uuid.UUID(id))
    )
    return NotificationRule.from_dataclass(action_result.rule_data)


@strawberry.field(description="List notification rules")
async def notification_rules(
    info: Info[StrawberryGQLContext],
    filter: Optional[NotificationRuleFilter] = None,
    order_by: Optional[NotificationRuleOrderBy] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> NotificationRuleConnection:
    processors = info.context.processors

    # Build querier from filter, order_by, and pagination
    querier = _build_rule_querier(
        filter=filter,
        order_by=order_by,
        first=first,
        after=after,
        last=last,
        before=before,
        limit=limit,
        offset=offset,
    )

    action_result = await processors.notification.list_rules.wait_for_complete(
        ListRulesAction(querier=querier)
    )

    nodes = [NotificationRule.from_dataclass(data) for data in action_result.rules]

    edges = [
        NotificationRuleEdge(node=node, cursor=to_global_id(NotificationRule, node.id))
        for node in nodes
    ]

    return NotificationRuleConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=False,
            has_previous_page=False,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
    )


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

    def to_creator(self, created_by: uuid.UUID) -> NotificationChannelCreator:
        return NotificationChannelCreator(
            name=self.name,
            description=self.description,
            channel_type=self.channel_type.to_internal(),
            config=self.config.to_dataclass(),
            enabled=self.enabled,
            created_by=created_by,
        )


@strawberry.input(description="Input for updating a notification channel")
class UpdateNotificationChannelInput:
    id: ID
    name: Optional[str] = UNSET
    description: Optional[str] = UNSET
    config: Optional[WebhookConfigInput] = UNSET
    enabled: Optional[bool] = UNSET

    def to_modifier(self) -> NotificationChannelModifier:
        config_state = OptionalState[WebhookConfig].nop()
        if self.config is not UNSET:
            if self.config is None:
                config_state = OptionalState[WebhookConfig].nop()
            else:
                config_state = OptionalState[WebhookConfig].update(self.config.to_dataclass())

        return NotificationChannelModifier(
            name=OptionalState[str].from_graphql(self.name),
            description=OptionalState[Optional[str]].from_graphql(self.description),
            config=config_state,
            enabled=OptionalState[bool].from_graphql(self.enabled),
        )


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

    def to_creator(self, created_by: uuid.UUID) -> NotificationRuleCreator:
        return NotificationRuleCreator(
            name=self.name,
            description=self.description,
            rule_type=self.rule_type.to_internal(),
            channel_id=uuid.UUID(self.channel_id),
            message_template=self.message_template,
            enabled=self.enabled,
            created_by=created_by,
        )


@strawberry.input(description="Input for updating a notification rule")
class UpdateNotificationRuleInput:
    id: ID
    name: Optional[str] = UNSET
    description: Optional[str] = UNSET
    message_template: Optional[str] = UNSET
    enabled: Optional[bool] = UNSET

    def to_modifier(self) -> NotificationRuleModifier:
        return NotificationRuleModifier(
            name=OptionalState[str].from_graphql(self.name),
            description=OptionalState[Optional[str]].from_graphql(self.description),
            message_template=OptionalState[str].from_graphql(self.message_template),
            enabled=OptionalState[bool].from_graphql(self.enabled),
        )


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


# Mutation fields


@strawberry.mutation(description="Create a new notification channel")
async def create_notification_channel(
    input: CreateNotificationChannelInput, info: Info[StrawberryGQLContext]
) -> CreateNotificationChannelPayload:
    processors = info.context.processors
    me = current_user()
    assert me is not None

    action_result = await processors.notification.create_channel.wait_for_complete(
        CreateChannelAction(creator=input.to_creator(me.user_id))
    )

    return CreateNotificationChannelPayload(
        channel=NotificationChannel.from_dataclass(action_result.channel_data)
    )


@strawberry.mutation(description="Update a notification channel")
async def update_notification_channel(
    input: UpdateNotificationChannelInput, info: Info[StrawberryGQLContext]
) -> UpdateNotificationChannelPayload:
    processors = info.context.processors

    action_result = await processors.notification.update_channel.wait_for_complete(
        UpdateChannelAction(
            channel_id=uuid.UUID(input.id),
            modifier=input.to_modifier(),
        )
    )

    return UpdateNotificationChannelPayload(
        channel=NotificationChannel.from_dataclass(action_result.channel_data)
    )


@strawberry.mutation(description="Delete a notification channel")
async def delete_notification_channel(
    input: DeleteNotificationChannelInput, info: Info[StrawberryGQLContext]
) -> DeleteNotificationChannelPayload:
    processors = info.context.processors

    await processors.notification.delete_channel.wait_for_complete(
        DeleteChannelAction(channel_id=uuid.UUID(input.id))
    )

    return DeleteNotificationChannelPayload(id=input.id)


@strawberry.mutation(description="Create a new notification rule")
async def create_notification_rule(
    input: CreateNotificationRuleInput, info: Info[StrawberryGQLContext]
) -> CreateNotificationRulePayload:
    processors = info.context.processors
    me = current_user()
    assert me is not None

    action_result = await processors.notification.create_rule.wait_for_complete(
        CreateRuleAction(creator=input.to_creator(me.user_id))
    )

    return CreateNotificationRulePayload(
        rule=NotificationRule.from_dataclass(action_result.rule_data)
    )


@strawberry.mutation(description="Update a notification rule")
async def update_notification_rule(
    input: UpdateNotificationRuleInput, info: Info[StrawberryGQLContext]
) -> UpdateNotificationRulePayload:
    processors = info.context.processors

    action_result = await processors.notification.update_rule.wait_for_complete(
        UpdateRuleAction(
            rule_id=uuid.UUID(input.id),
            modifier=input.to_modifier(),
        )
    )

    return UpdateNotificationRulePayload(
        rule=NotificationRule.from_dataclass(action_result.rule_data)
    )


@strawberry.mutation(description="Delete a notification rule")
async def delete_notification_rule(
    input: DeleteNotificationRuleInput, info: Info[StrawberryGQLContext]
) -> DeleteNotificationRulePayload:
    processors = info.context.processors

    await processors.notification.delete_rule.wait_for_complete(
        DeleteRuleAction(rule_id=uuid.UUID(input.id))
    )

    return DeleteNotificationRulePayload(id=input.id)
