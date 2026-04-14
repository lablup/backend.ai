"""Access token GraphQL types for model deployment."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any, Self, cast
from uuid import UUID

from strawberry import ID, Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.deployment.request import (
    AccessTokenFilter as AccessTokenFilterDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    AccessTokenOrder as AccessTokenOrderDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    CreateAccessTokenInput as CreateAccessTokenInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    DeleteAccessTokenInput as DeleteAccessTokenInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.response import (
    AccessTokenNode as AccessTokenNodeDTO,
)
from ai.backend.common.dto.manager.v2.deployment.response import (
    CreateAccessTokenPayload as CreateAccessTokenPayloadDTO,
)
from ai.backend.common.dto.manager.v2.deployment.response import (
    DeleteAccessTokenPayload as DeleteAccessTokenPayloadDTO,
)
from ai.backend.common.dto.manager.v2.deployment.types import (
    AccessTokenOrderField,
)
from ai.backend.manager.api.gql.base import DateTimeFilter, OrderDirection, StringFilter
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_connection_type,
    gql_field,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.16.0"),
    name="AccessTokenFilter",
)
class AccessTokenFilter(PydanticInputMixin[AccessTokenFilterDTO]):
    """Filter for access tokens."""

    token: StringFilter | None = None
    expires_at: DateTimeFilter | None = None
    created_at: DateTimeFilter | None = None

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.16.0"),
)
class AccessTokenOrderBy(PydanticInputMixin[AccessTokenOrderDTO]):
    field: AccessTokenOrderField
    direction: OrderDirection = OrderDirection.DESC


@gql_node_type(
    BackendAIGQLMeta(added_version="25.16.0", description="An access token for model deployment.")
)
class AccessToken(PydanticNodeMixin[AccessTokenNodeDTO]):
    id: NodeID[str]
    token: str = gql_field(description="The access token.")
    created_at: datetime = gql_field(description="The creation timestamp of the access token.")
    expires_at: datetime | None = gql_field(
        description="The expiration timestamp of the access token."
    )

    @classmethod
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.access_token_loader.load_many([
            UUID(nid) for nid in node_ids
        ])
        return cast(list[Self | None], results)


AccessTokenEdge = Edge[AccessToken]


@gql_connection_type(
    BackendAIGQLMeta(added_version="25.16.0", description="Connection for access tokens.")
)
class AccessTokenConnection(Connection[AccessToken]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for creating an access token for a model deployment.",
        added_version="25.16.0",
    ),
)
class CreateAccessTokenInput(PydanticInputMixin[CreateAccessTokenInputDTO]):
    model_deployment_id: ID = gql_field(
        description="The ID of the model deployment for which the access token is created."
    )
    expires_at: datetime | None = gql_field(
        description="The expiration timestamp of the access token."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(added_version="25.16.0", description="Payload for creating an access token."),
    model=CreateAccessTokenPayloadDTO,
)
class CreateAccessTokenPayload:
    access_token: AccessToken


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for deleting an access token.",
        added_version="25.16.0",
    ),
)
class DeleteAccessTokenInput(PydanticInputMixin[DeleteAccessTokenInputDTO]):
    id: ID = gql_field(description="The ID of the access token to delete.")


@gql_pydantic_type(
    BackendAIGQLMeta(added_version="25.16.0", description="Payload for deleting an access token."),
    model=DeleteAccessTokenPayloadDTO,
)
class DeleteAccessTokenPayload:
    id: UUID
