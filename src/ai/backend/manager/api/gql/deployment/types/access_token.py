"""Access token GraphQL types for model deployment."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any, Self
from uuid import UUID

import strawberry
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
from ai.backend.common.dto.manager.v2.deployment.response import (
    AccessTokenNode as AccessTokenNodeDTO,
)
from ai.backend.common.dto.manager.v2.deployment.response import (
    CreateAccessTokenPayload as CreateAccessTokenPayloadDTO,
)
from ai.backend.common.dto.manager.v2.deployment.types import (
    AccessTokenOrderField as DTOAccessTokenOrderField,
)
from ai.backend.common.dto.manager.v2.deployment.types import (
    OrderDirection as DTOOrderDirection,
)
from ai.backend.manager.api.gql.base import DateTimeFilter, OrderDirection, StringFilter
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.data.deployment.types import (
    AccessTokenOrderField,
    ModelDeploymentAccessTokenData,
)


@strawberry.experimental.pydantic.input(
    model=AccessTokenFilterDTO,
    description="Added in 25.16.0",
)
class AccessTokenFilter:
    """Filter for access tokens."""

    token: StringFilter | None = None
    valid_until: DateTimeFilter | None = None
    created_at: DateTimeFilter | None = None

    AND: list[AccessTokenFilter] | None = None
    OR: list[AccessTokenFilter] | None = None
    NOT: list[AccessTokenFilter] | None = None

    def to_pydantic(self) -> AccessTokenFilterDTO:
        return AccessTokenFilterDTO(
            token=self.token.to_pydantic() if self.token else None,
            valid_until=self.valid_until.to_pydantic() if self.valid_until else None,
            created_at=self.created_at.to_pydantic() if self.created_at else None,
            AND=[f.to_pydantic() for f in self.AND] if self.AND else None,
            OR=[f.to_pydantic() for f in self.OR] if self.OR else None,
            NOT=[f.to_pydantic() for f in self.NOT] if self.NOT else None,
        )


@strawberry.experimental.pydantic.input(
    model=AccessTokenOrderDTO,
    description="Added in 25.16.0",
)
class AccessTokenOrderBy:
    field: AccessTokenOrderField
    direction: OrderDirection = OrderDirection.DESC

    def to_pydantic(self) -> AccessTokenOrderDTO:
        return AccessTokenOrderDTO(
            field=DTOAccessTokenOrderField(self.field.value.lower()),
            direction=DTOOrderDirection(self.direction.value.lower()),
        )


@strawberry.type
class AccessToken(PydanticNodeMixin[AccessTokenNodeDTO]):
    id: NodeID[str]
    token: str = strawberry.field(description="Added in 25.16.0: The access token.")
    created_at: datetime = strawberry.field(
        description="Added in 25.16.0: The creation timestamp of the access token."
    )
    valid_until: datetime = strawberry.field(
        description="Added in 25.16.0: The expiration timestamp of the access token."
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
        return [cls.from_dataclass(data) if data is not None else None for data in results]

    @classmethod
    def from_dataclass(cls, data: ModelDeploymentAccessTokenData) -> Self:
        return cls(
            id=ID(str(data.id)),
            token=data.token,
            created_at=data.created_at,
            valid_until=data.valid_until,
        )

    @classmethod
    def from_pydantic(
        cls,
        dto: AccessTokenNodeDTO,
        *,
        id_field: str = "id",
        extra: dict[str, Any] | None = None,
    ) -> Self:
        return cls(
            id=ID(str(dto.id)),
            token=dto.token,
            created_at=dto.created_at,
            valid_until=dto.valid_until,
        )


AccessTokenEdge = Edge[AccessToken]


@strawberry.type(description="Added in 25.16.0")
class AccessTokenConnection(Connection[AccessToken]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@strawberry.experimental.pydantic.input(
    model=CreateAccessTokenInputDTO,
    description="Added in 25.16.0. Input for creating an access token for a model deployment.",
)
class CreateAccessTokenInput:
    model_deployment_id: ID = strawberry.field(
        description="Added in 25.16.0: The ID of the model deployment for which the access token is created."
    )
    valid_until: datetime = strawberry.field(
        description="Added in 25.16.0: The expiration timestamp of the access token."
    )

    def to_pydantic(self) -> CreateAccessTokenInputDTO:
        return CreateAccessTokenInputDTO(
            deployment_id=UUID(self.model_deployment_id),
            valid_until=self.valid_until,
        )


@strawberry.experimental.pydantic.type(
    model=CreateAccessTokenPayloadDTO,
    description="Added in 25.16.0",
)
class CreateAccessTokenPayload:
    access_token: AccessToken
