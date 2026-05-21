"""LoginHistory GraphQL Node, Edge, and Connection types."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Any
from uuid import UUID

import strawberry
from strawberry import Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.login_history.response import LoginHistoryNode
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
    from ai.backend.manager.api.gql.domain_v2.types.node import DomainV2GQL
    from ai.backend.manager.api.gql.user.types.node import UserV2GQL


@gql_enum(
    BackendAIGQLMeta(added_version="26.4.2", description="Result of a login attempt."),
    name="LoginAttemptResult",
)
class LoginAttemptResultGQL(StrEnum):
    SUCCESS = "success"
    FAILED_INVALID_CREDENTIALS = "failed_invalid_credentials"
    FAILED_USER_INACTIVE = "failed_user_inactive"
    FAILED_BLOCKED = "failed_blocked"
    FAILED_PASSWORD_EXPIRED = "failed_password_expired"
    FAILED_REJECTED_BY_HOOK = "failed_rejected_by_hook"
    FAILED_SESSION_ALREADY_EXISTS = "failed_session_already_exists"
    LOGOUT = "logout"
    REVOKED_BY_ADMIN = "revoked_by_admin"
    REVOKED_BY_USER = "revoked_by_user"
    EVICTED = "evicted"
    EXPIRED = "expired"


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Represents a login history entry tracking user authentication attempts.",
    ),
    name="LoginHistoryV2",
)
class LoginHistoryV2GQL(PydanticNodeMixin[LoginHistoryNode]):
    id: NodeID[str] = gql_field(description="Unique identifier of the login history entry (UUID).")

    user_id: UUID = gql_field(description="UUID of the user who attempted to log in.")
    domain_name: str = gql_field(description="Domain name of the user at the time of the attempt.")
    result: LoginAttemptResultGQL = gql_field(description="Result of the login attempt.")
    fail_reason: str | None = gql_field(description="Detailed reason for the login failure.")
    created_at: datetime = gql_field(description="Timestamp when the login attempt occurred.")

    client_ip: str | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Client IP that initiated the event. Null for system-driven events (e.g. eviction, expiration).",
        )
    )

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.3",
            description="The user who attempted to log in.",
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

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.3",
            description="The domain at the time of the login attempt.",
        )
    )  # type: ignore[misc]
    async def domain(
        self,
        info: Info[StrawberryGQLContext],
    ) -> (
        Annotated[
            DomainV2GQL,
            strawberry.lazy("ai.backend.manager.api.gql.domain_v2.types.node"),
        ]
        | None
    ):
        return await info.context.data_loaders.domain_loader.load(self.domain_name)


LoginHistoryV2EdgeGQL = Edge[LoginHistoryV2GQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Connection type for paginated login history results.",
    ),
    name="LoginHistoryV2Connection",
)
class LoginHistoryV2ConnectionGQL(Connection[LoginHistoryV2GQL]):
    count: int = gql_field(description="Total number of login history entries matching the query.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
