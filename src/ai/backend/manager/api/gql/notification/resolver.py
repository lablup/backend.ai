"""GraphQL query and mutation resolvers for notification system."""

from __future__ import annotations

import uuid
from typing import Optional

import strawberry
from strawberry import ID, UNSET, Info
from strawberry.relay import Connection, Edge

from ai.backend.common.contexts.user import current_user
from ai.backend.manager.api.gql.base import to_global_id
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
    UpdateNotificationChannelInput,
    UpdateNotificationChannelPayload,
    UpdateNotificationRuleInput,
    UpdateNotificationRulePayload,
    ValidateNotificationChannelInput,
    ValidateNotificationChannelPayload,
    ValidateNotificationRuleInput,
    ValidateNotificationRulePayload,
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
    order_by: Optional[NotificationChannelOrderBy] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> NotificationChannelConnection:
    processors = info.context.processors

    # Build querier from filter, order_by, and pagination using adapter
    querier = info.context.gql_adapters.notification_channel.build_querier(
        filter=filter,
        order_by=order_by,
        first=first,
        after=after,
        last=last,
        before=before,
        limit=limit,
        offset=offset,
    )

    action_result = await processors.notification.search_channels.wait_for_complete(
        SearchChannelsAction(querier=querier)
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
    order_by: Optional[NotificationRuleOrderBy] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> NotificationRuleConnection:
    processors = info.context.processors

    # Build querier from filter, order_by, and pagination using adapter
    querier = info.context.gql_adapters.notification_rule.build_querier(
        filter=filter,
        order_by=order_by,
        first=first,
        after=after,
        last=last,
        before=before,
        limit=limit,
        offset=offset,
    )

    action_result = await processors.notification.search_rules.wait_for_complete(
        SearchRulesAction(querier=querier)
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
        count=action_result.total_count,
    )


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
