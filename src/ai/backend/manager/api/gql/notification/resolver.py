"""GraphQL query and mutation resolvers for notification system."""

from __future__ import annotations

import uuid
from functools import lru_cache
from typing import Optional

import strawberry
from strawberry import ID, UNSET, Info
from strawberry.relay import Connection, Edge

from ai.backend.common.contexts.user import current_user
from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.errors.auth import InvalidAuthParameters
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
    SearchChannelsAction,
    SearchRulesAction,
    UpdateChannelAction,
    UpdateRuleAction,
    ValidateChannelAction,
    ValidateRuleAction,
)

from ..types import StrawberryGQLContext
from .types import (
    CreateNotificationChannelInput,
    CreateNotificationChannelPayload,
    CreateNotificationRuleInput,
    CreateNotificationRulePayload,
    DeleteNotificationChannelInput,
    DeleteNotificationChannelPayload,
    DeleteNotificationRuleInput,
    DeleteNotificationRulePayload,
    NotificationChannel,
    NotificationChannelFilter,
    NotificationChannelOrderBy,
    NotificationRule,
    NotificationRuleFilter,
    NotificationRuleOrderBy,
    NotificationRuleTypeGQL,
    UpdateNotificationChannelInput,
    UpdateNotificationChannelPayload,
    UpdateNotificationRuleInput,
    UpdateNotificationRulePayload,
    ValidateNotificationChannelInput,
    ValidateNotificationChannelPayload,
    ValidateNotificationRuleInput,
    ValidateNotificationRulePayload,
)

# Pagination specs


@lru_cache(maxsize=1)
def _get_channel_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=NotificationChannelOrders.created_at(ascending=False),
        backward_order=NotificationChannelOrders.created_at(ascending=True),
        forward_condition_factory=NotificationChannelConditions.by_cursor_forward,
        backward_condition_factory=NotificationChannelConditions.by_cursor_backward,
    )


@lru_cache(maxsize=1)
def _get_rule_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=NotificationRuleOrders.created_at(ascending=False),
        backward_order=NotificationRuleOrders.created_at(ascending=True),
        forward_condition_factory=NotificationRuleConditions.by_cursor_forward,
        backward_condition_factory=NotificationRuleConditions.by_cursor_backward,
    )


# Connection types

NotificationChannelEdge = Edge[NotificationChannel]


@strawberry.type(description="Notification channel connection")
class NotificationChannelConnection(Connection[NotificationChannel]):
    count: int

    def __init__(self, *args, count: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.count = count


NotificationRuleEdge = Edge[NotificationRule]


@strawberry.type(description="Notification rule connection")
class NotificationRuleConnection(Connection[NotificationRule]):
    count: int

    def __init__(self, *args, count: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.count = count


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
    order_by: Optional[list[NotificationChannelOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> NotificationChannelConnection:
    processors = info.context.processors

    # Build querier from filter, order_by, and pagination using adapter
    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        _get_channel_pagination_spec(),
        filter=filter,
        order_by=order_by,
    )

    action_result = await processors.notification.search_channels.wait_for_complete(
        SearchChannelsAction(querier=querier)
    )

    nodes = [NotificationChannel.from_dataclass(data) for data in action_result.channels]

    edges = [
        NotificationChannelEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes
    ]

    return NotificationChannelConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
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
    order_by: Optional[list[NotificationRuleOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> NotificationRuleConnection:
    processors = info.context.processors

    # Build querier from filter, order_by, and pagination using adapter
    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        _get_rule_pagination_spec(),
        filter=filter,
        order_by=order_by,
    )

    action_result = await processors.notification.search_rules.wait_for_complete(
        SearchRulesAction(querier=querier)
    )

    nodes = [NotificationRule.from_dataclass(data) for data in action_result.rules]

    edges = [NotificationRuleEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return NotificationRuleConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )


@strawberry.field(description="List available notification rule types")
async def notification_rule_types() -> list[NotificationRuleTypeGQL]:
    """Return all available notification rule types."""
    from ai.backend.common.data.notification import NotificationRuleType

    return [NotificationRuleTypeGQL.from_internal(rt) for rt in NotificationRuleType]


@strawberry.field(description="Get JSON schema for a notification rule type's message format")
async def notification_rule_type_schema(
    rule_type: NotificationRuleTypeGQL,
) -> strawberry.scalars.JSON:
    """Return the JSON schema for a given notification rule type."""
    from ai.backend.common.data.notification import NotifiableMessage

    # Convert GraphQL enum to internal enum and get schema
    internal_type = rule_type.to_internal()
    schema = NotifiableMessage.get_message_schema(internal_type)
    return schema


# Mutation fields


@strawberry.mutation(description="Create a new notification channel")
async def create_notification_channel(
    input: CreateNotificationChannelInput, info: Info[StrawberryGQLContext]
) -> CreateNotificationChannelPayload:
    processors = info.context.processors
    me = current_user()
    if me is None:
        raise InvalidAuthParameters("User authentication is required")

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

    channel_id = uuid.UUID(input.id)
    action_result = await processors.notification.update_channel.wait_for_complete(
        UpdateChannelAction(updater=input.to_updater(channel_id))
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
    if me is None:
        raise InvalidAuthParameters("User authentication is required")

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

    rule_id = uuid.UUID(input.id)
    action_result = await processors.notification.update_rule.wait_for_complete(
        UpdateRuleAction(updater=input.to_updater(rule_id))
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


@strawberry.mutation(description="Validate a notification channel")
async def validate_notification_channel(
    input: ValidateNotificationChannelInput, info: Info[StrawberryGQLContext]
) -> ValidateNotificationChannelPayload:
    processors = info.context.processors

    await processors.notification.validate_channel.wait_for_complete(
        ValidateChannelAction(
            channel_id=uuid.UUID(input.id),
            test_message=input.test_message,
        )
    )

    return ValidateNotificationChannelPayload(
        id=input.id,
    )


@strawberry.mutation(description="Validate a notification rule")
async def validate_notification_rule(
    input: ValidateNotificationRuleInput, info: Info[StrawberryGQLContext]
) -> ValidateNotificationRulePayload:
    processors = info.context.processors

    notification_data = {}
    if input.notification_data is not UNSET and input.notification_data is not None:
        notification_data = dict(input.notification_data)

    action_result = await processors.notification.validate_rule.wait_for_complete(
        ValidateRuleAction(
            rule_id=uuid.UUID(input.id),
            notification_data=notification_data,
        )
    )

    return ValidateNotificationRulePayload(
        message=action_result.message,
    )
