"""LoginSession GraphQL Node, Edge, and Connection types."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Any
from uuid import UUID

import strawberry
from strawberry import Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.login_session.response import LoginSessionNode
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_added_field,
    gql_connection_type,
    gql_enum,
    gql_field,
    gql_node_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.user.types.node import UserV2GQL


@gql_enum(
    BackendAIGQLMeta(added_version="26.4.2", description="Status of a login session."),
    name="LoginSessionStatus",
)
class LoginSessionStatusGQL(StrEnum):
    ACTIVE = "active"
    INVALIDATED = "invalidated"
    REVOKED = "revoked"


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Represents a login session entry tracking user authentication sessions.",
    ),
    name="LoginSessionV2",
)
class LoginSessionV2GQL(PydanticNodeMixin[LoginSessionNode]):
    id: NodeID[str] = gql_field(description="Unique identifier of the login session (UUID).")

    user_id: UUID = gql_field(description="UUID of the user who owns the session.")
    access_key: str = gql_field(description="Access key associated with the session.")
    status: LoginSessionStatusGQL = gql_field(description="Current status of the login session.")
    created_at: datetime = gql_field(description="Timestamp when the session was created.")
    last_accessed_at: datetime | None = gql_field(
        description="Timestamp when the session was last accessed."
    )
    invalidated_at: datetime | None = gql_field(
        description="Timestamp when the session was invalidated."
    )
    client_ip: str | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Originating client IP of the login that created this session, if known.",
        ),
        default=None,
    )

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.3",
            description="The user who owns this login session.",
        )
    )  # type: ignore[misc]
    async def user(
        self,
        info: Info[StrawberryGQLContext],
    ) -> (
        Annotated[
            UserV2GQL,
            strawberry.lazy("ai.backend.manager.api.gql.user.types.node"),
        ]
        | None
    ):
        return await info.context.data_loaders.user_loader.load(self.user_id)


LoginSessionV2EdgeGQL = Edge[LoginSessionV2GQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Connection type for paginated login session results.",
    ),
    name="LoginSessionV2Connection",
)
class LoginSessionV2ConnectionGQL(Connection[LoginSessionV2GQL]):
    count: int = gql_field(description="Total number of login sessions matching the query.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
