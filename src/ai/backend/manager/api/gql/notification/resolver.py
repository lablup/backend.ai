"""GraphQL query and mutation resolvers for notification system."""

from __future__ import annotations

import uuid
from typing import Any

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge

from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.v2.notification.request import (
    SearchNotificationChannelsInput,
    SearchNotificationRulesInput,
)
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only
from ai.backend.manager.errors.auth import InvalidAuthParameters

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

# Connection types

NotificationChannelEdge = Edge[NotificationChannel]


@strawberry.type(description="Notification channel connection")
class NotificationChannelConnection(Connection[NotificationChannel]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


NotificationRuleEdge = Edge[NotificationRule]


@strawberry.type(description="Notification rule connection")
class NotificationRuleConnection(Connection[NotificationRule]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


# Query fields


@strawberry.field(description="Get a notification channel by ID (admin only)")  # type: ignore[misc]
async def admin_notification_channel(
    id: ID, info: Info[StrawberryGQLContext]
) -> NotificationChannel | None:
    check_admin_only()
    result = await info.context.adapters.notification.get_channel(uuid.UUID(id))
    return NotificationChannel.from_pydantic(result.item)


@strawberry.field(  # type: ignore[misc]
    description="Get a notification channel by ID",
    deprecation_reason=(
        "Use admin_notification_channel instead. "
        "This API will be removed after v26.3.0. See BEP-1041 for migration guide."
    ),
)
async def notification_channel(
    id: ID, info: Info[StrawberryGQLContext]
) -> NotificationChannel | None:
    result = await info.context.adapters.notification.get_channel(uuid.UUID(id))
    return NotificationChannel.from_pydantic(result.item)


@strawberry.field(description="List notification channels (admin only)")  # type: ignore[misc]
async def admin_notification_channels(
    info: Info[StrawberryGQLContext],
    filter: NotificationChannelFilter | None = None,
    order_by: list[NotificationChannelOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> NotificationChannelConnection | None:
    check_admin_only()

    pydantic_filter = filter.to_pydantic() if filter is not None else None
    pydantic_orders = [o.to_pydantic() for o in order_by] if order_by is not None else None
    payload = await info.context.adapters.notification.search_channels(
        SearchNotificationChannelsInput(
            filter=pydantic_filter,
            order=pydantic_orders,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )

    nodes = [NotificationChannel.from_pydantic(item) for item in payload.items]
    edges = [
        NotificationChannelEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes
    ]

    return NotificationChannelConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )


@strawberry.field(  # type: ignore[misc]
    description="List notification channels",
    deprecation_reason=(
        "Use admin_notification_channels instead. "
        "This API will be removed after v26.3.0. See BEP-1041 for migration guide."
    ),
)
async def notification_channels(
    info: Info[StrawberryGQLContext],
    filter: NotificationChannelFilter | None = None,
    order_by: list[NotificationChannelOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> NotificationChannelConnection | None:
    pydantic_filter = filter.to_pydantic() if filter is not None else None
    pydantic_orders = [o.to_pydantic() for o in order_by] if order_by is not None else None
    payload = await info.context.adapters.notification.search_channels(
        SearchNotificationChannelsInput(
            filter=pydantic_filter,
            order=pydantic_orders,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )

    nodes = [NotificationChannel.from_pydantic(item) for item in payload.items]
    edges = [
        NotificationChannelEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes
    ]

    return NotificationChannelConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )


@strawberry.field(description="Get a notification rule by ID (admin only)")  # type: ignore[misc]
async def admin_notification_rule(
    id: ID, info: Info[StrawberryGQLContext]
) -> NotificationRule | None:
    check_admin_only()
    result = await info.context.adapters.notification.get_rule(uuid.UUID(id))
    return NotificationRule.from_pydantic(result.item)


@strawberry.field(  # type: ignore[misc]
    description="Get a notification rule by ID",
    deprecation_reason=(
        "Use admin_notification_rule instead. "
        "This API will be removed after v26.3.0. See BEP-1041 for migration guide."
    ),
)
async def notification_rule(id: ID, info: Info[StrawberryGQLContext]) -> NotificationRule | None:
    result = await info.context.adapters.notification.get_rule(uuid.UUID(id))
    return NotificationRule.from_pydantic(result.item)


@strawberry.field(description="List notification rules (admin only)")  # type: ignore[misc]
async def admin_notification_rules(
    info: Info[StrawberryGQLContext],
    filter: NotificationRuleFilter | None = None,
    order_by: list[NotificationRuleOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> NotificationRuleConnection | None:
    check_admin_only()

    pydantic_filter = filter.to_pydantic() if filter is not None else None
    pydantic_orders = [o.to_pydantic() for o in order_by] if order_by is not None else None
    payload = await info.context.adapters.notification.search_rules(
        SearchNotificationRulesInput(
            filter=pydantic_filter,
            order=pydantic_orders,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )

    nodes = [NotificationRule.from_pydantic(item) for item in payload.items]
    edges = [NotificationRuleEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return NotificationRuleConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )


@strawberry.field(  # type: ignore[misc]
    description="List notification rules",
    deprecation_reason=(
        "Use admin_notification_rules instead. "
        "This API will be removed after v26.3.0. See BEP-1041 for migration guide."
    ),
)
async def notification_rules(
    info: Info[StrawberryGQLContext],
    filter: NotificationRuleFilter | None = None,
    order_by: list[NotificationRuleOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> NotificationRuleConnection | None:
    pydantic_filter = filter.to_pydantic() if filter is not None else None
    pydantic_orders = [o.to_pydantic() for o in order_by] if order_by is not None else None
    payload = await info.context.adapters.notification.search_rules(
        SearchNotificationRulesInput(
            filter=pydantic_filter,
            order=pydantic_orders,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )

    nodes = [NotificationRule.from_pydantic(item) for item in payload.items]
    edges = [NotificationRuleEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return NotificationRuleConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )


@strawberry.field(description="List available notification rule types")  # type: ignore[misc]
async def notification_rule_types() -> list[NotificationRuleTypeGQL] | None:
    """Return all available notification rule types."""
    from ai.backend.common.data.notification import NotificationRuleType

    return [NotificationRuleTypeGQL.from_internal(rt) for rt in NotificationRuleType]


@strawberry.field(description="Get JSON schema for a notification rule type's message format")  # type: ignore[misc]
async def notification_rule_type_schema(
    rule_type: NotificationRuleTypeGQL,
) -> strawberry.scalars.JSON:
    """Return the JSON schema for a given notification rule type."""
    from ai.backend.common.data.notification import NotifiableMessage

    internal_type = rule_type.to_internal()
    return NotifiableMessage.get_message_schema(internal_type)


# Mutation fields


@strawberry.mutation(description="Create a new notification channel (admin only)")  # type: ignore[misc]
async def admin_create_notification_channel(
    input: CreateNotificationChannelInput, info: Info[StrawberryGQLContext]
) -> CreateNotificationChannelPayload:
    check_admin_only()
    me = current_user()
    if me is None:
        raise InvalidAuthParameters("User authentication is required")
    result = await info.context.adapters.notification.create_channel(
        input.to_pydantic(), me.user_id
    )
    return CreateNotificationChannelPayload.from_pydantic(result)


@strawberry.mutation(  # type: ignore[misc]
    description="Create a new notification channel",
    deprecation_reason=(
        "Use admin_create_notification_channel instead. "
        "This API will be removed after v26.3.0. See BEP-1041 for migration guide."
    ),
)
async def create_notification_channel(
    input: CreateNotificationChannelInput, info: Info[StrawberryGQLContext]
) -> CreateNotificationChannelPayload:
    me = current_user()
    if me is None:
        raise InvalidAuthParameters("User authentication is required")
    result = await info.context.adapters.notification.create_channel(
        input.to_pydantic(), me.user_id
    )
    return CreateNotificationChannelPayload.from_pydantic(result)


@strawberry.mutation(description="Update a notification channel (admin only)")  # type: ignore[misc]
async def admin_update_notification_channel(
    input: UpdateNotificationChannelInput, info: Info[StrawberryGQLContext]
) -> UpdateNotificationChannelPayload:
    check_admin_only()
    channel_id = uuid.UUID(input.id)
    result = await info.context.adapters.notification.update_channel(
        channel_id, input.to_pydantic()
    )
    return UpdateNotificationChannelPayload.from_pydantic(result)


@strawberry.mutation(  # type: ignore[misc]
    description="Update a notification channel",
    deprecation_reason=(
        "Use admin_update_notification_channel instead. "
        "This API will be removed after v26.3.0. See BEP-1041 for migration guide."
    ),
)
async def update_notification_channel(
    input: UpdateNotificationChannelInput, info: Info[StrawberryGQLContext]
) -> UpdateNotificationChannelPayload:
    channel_id = uuid.UUID(input.id)
    result = await info.context.adapters.notification.update_channel(
        channel_id, input.to_pydantic()
    )
    return UpdateNotificationChannelPayload.from_pydantic(result)


@strawberry.mutation(description="Delete a notification channel (admin only)")  # type: ignore[misc]
async def admin_delete_notification_channel(
    input: DeleteNotificationChannelInput, info: Info[StrawberryGQLContext]
) -> DeleteNotificationChannelPayload:
    check_admin_only()
    result = await info.context.adapters.notification.delete_channel(input.to_pydantic())
    return DeleteNotificationChannelPayload.from_pydantic(result)


@strawberry.mutation(  # type: ignore[misc]
    description="Delete a notification channel",
    deprecation_reason=(
        "Use admin_delete_notification_channel instead. "
        "This API will be removed after v26.3.0. See BEP-1041 for migration guide."
    ),
)
async def delete_notification_channel(
    input: DeleteNotificationChannelInput, info: Info[StrawberryGQLContext]
) -> DeleteNotificationChannelPayload:
    result = await info.context.adapters.notification.delete_channel(input.to_pydantic())
    return DeleteNotificationChannelPayload.from_pydantic(result)


@strawberry.mutation(description="Create a new notification rule (admin only)")  # type: ignore[misc]
async def admin_create_notification_rule(
    input: CreateNotificationRuleInput, info: Info[StrawberryGQLContext]
) -> CreateNotificationRulePayload:
    check_admin_only()
    me = current_user()
    if me is None:
        raise InvalidAuthParameters("User authentication is required")
    result = await info.context.adapters.notification.create_rule(input.to_pydantic(), me.user_id)
    return CreateNotificationRulePayload.from_pydantic(result)


@strawberry.mutation(  # type: ignore[misc]
    description="Create a new notification rule",
    deprecation_reason=(
        "Use admin_create_notification_rule instead. "
        "This API will be removed after v26.3.0. See BEP-1041 for migration guide."
    ),
)
async def create_notification_rule(
    input: CreateNotificationRuleInput, info: Info[StrawberryGQLContext]
) -> CreateNotificationRulePayload:
    me = current_user()
    if me is None:
        raise InvalidAuthParameters("User authentication is required")
    result = await info.context.adapters.notification.create_rule(input.to_pydantic(), me.user_id)
    return CreateNotificationRulePayload.from_pydantic(result)


@strawberry.mutation(description="Update a notification rule (admin only)")  # type: ignore[misc]
async def admin_update_notification_rule(
    input: UpdateNotificationRuleInput, info: Info[StrawberryGQLContext]
) -> UpdateNotificationRulePayload:
    check_admin_only()
    rule_id = uuid.UUID(input.id)
    result = await info.context.adapters.notification.update_rule(rule_id, input.to_pydantic())
    return UpdateNotificationRulePayload.from_pydantic(result)


@strawberry.mutation(  # type: ignore[misc]
    description="Update a notification rule",
    deprecation_reason=(
        "Use admin_update_notification_rule instead. "
        "This API will be removed after v26.3.0. See BEP-1041 for migration guide."
    ),
)
async def update_notification_rule(
    input: UpdateNotificationRuleInput, info: Info[StrawberryGQLContext]
) -> UpdateNotificationRulePayload:
    rule_id = uuid.UUID(input.id)
    result = await info.context.adapters.notification.update_rule(rule_id, input.to_pydantic())
    return UpdateNotificationRulePayload.from_pydantic(result)


@strawberry.mutation(description="Delete a notification rule (admin only)")  # type: ignore[misc]
async def admin_delete_notification_rule(
    input: DeleteNotificationRuleInput, info: Info[StrawberryGQLContext]
) -> DeleteNotificationRulePayload:
    check_admin_only()
    result = await info.context.adapters.notification.delete_rule(input.to_pydantic())
    return DeleteNotificationRulePayload.from_pydantic(result)


@strawberry.mutation(  # type: ignore[misc]
    description="Delete a notification rule",
    deprecation_reason=(
        "Use admin_delete_notification_rule instead. "
        "This API will be removed after v26.3.0. See BEP-1041 for migration guide."
    ),
)
async def delete_notification_rule(
    input: DeleteNotificationRuleInput, info: Info[StrawberryGQLContext]
) -> DeleteNotificationRulePayload:
    result = await info.context.adapters.notification.delete_rule(input.to_pydantic())
    return DeleteNotificationRulePayload.from_pydantic(result)


@strawberry.mutation(description="Validate a notification channel (admin only)")  # type: ignore[misc]
async def admin_validate_notification_channel(
    input: ValidateNotificationChannelInput, info: Info[StrawberryGQLContext]
) -> ValidateNotificationChannelPayload:
    check_admin_only()
    result = await info.context.adapters.notification.validate_channel(input.to_pydantic())
    return ValidateNotificationChannelPayload(id=ID(str(result.channel_id)))


@strawberry.mutation(  # type: ignore[misc]
    description="Validate a notification channel",
    deprecation_reason=(
        "Use admin_validate_notification_channel instead. "
        "This API will be removed after v26.3.0. See BEP-1041 for migration guide."
    ),
)
async def validate_notification_channel(
    input: ValidateNotificationChannelInput, info: Info[StrawberryGQLContext]
) -> ValidateNotificationChannelPayload:
    result = await info.context.adapters.notification.validate_channel(input.to_pydantic())
    return ValidateNotificationChannelPayload(id=ID(str(result.channel_id)))


@strawberry.mutation(description="Validate a notification rule (admin only)")  # type: ignore[misc]
async def admin_validate_notification_rule(
    input: ValidateNotificationRuleInput, info: Info[StrawberryGQLContext]
) -> ValidateNotificationRulePayload:
    check_admin_only()
    result = await info.context.adapters.notification.validate_rule(input.to_pydantic())
    return ValidateNotificationRulePayload.from_pydantic(result)


@strawberry.mutation(  # type: ignore[misc]
    description="Validate a notification rule",
    deprecation_reason=(
        "Use admin_validate_notification_rule instead. "
        "This API will be removed after v26.3.0. See BEP-1041 for migration guide."
    ),
)
async def validate_notification_rule(
    input: ValidateNotificationRuleInput, info: Info[StrawberryGQLContext]
) -> ValidateNotificationRulePayload:
    result = await info.context.adapters.notification.validate_rule(input.to_pydantic())
    return ValidateNotificationRulePayload.from_pydantic(result)
