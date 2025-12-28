"""Access token GraphQL types for model deployment."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Self, override
from uuid import UUID

import strawberry
from strawberry import ID
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.manager.api.gql.base import DateTimeFilter, OrderDirection, StringFilter
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy
from ai.backend.manager.data.deployment.access_token import ModelDeploymentAccessTokenCreator
from ai.backend.manager.data.deployment.types import (
    AccessTokenOrderField,
    ModelDeploymentAccessTokenData,
)
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder
from ai.backend.manager.repositories.deployment.options import (
    AccessTokenConditions,
    AccessTokenOrders,
)


@strawberry.input(description="Added in 25.16.0")
class AccessTokenFilter(GQLFilter):
    """Filter for access tokens."""

    token: Optional[StringFilter] = None
    valid_until: Optional[DateTimeFilter] = None
    created_at: Optional[DateTimeFilter] = None

    @override
    def build_conditions(self) -> list[QueryCondition]:
        """Build query conditions from this filter."""
        conditions: list[QueryCondition] = []

        if self.token:
            if self.token.equals:
                conditions.append(AccessTokenConditions.by_token_equals(self.token.equals))
            elif self.token.contains:
                conditions.append(AccessTokenConditions.by_token_contains(self.token.contains))

        if self.valid_until:
            condition = self.valid_until.build_query_condition(
                before_factory=AccessTokenConditions.by_valid_until_before,
                after_factory=AccessTokenConditions.by_valid_until_after,
                equals_factory=AccessTokenConditions.by_valid_until_equals,
            )
            if condition:
                conditions.append(condition)

        if self.created_at:
            condition = self.created_at.build_query_condition(
                before_factory=AccessTokenConditions.by_created_at_before,
                after_factory=AccessTokenConditions.by_created_at_after,
                equals_factory=AccessTokenConditions.by_created_at_equals,
            )
            if condition:
                conditions.append(condition)

        return conditions


@strawberry.input(description="Added in 25.16.0")
class AccessTokenOrderBy(GQLOrderBy):
    field: AccessTokenOrderField
    direction: OrderDirection = OrderDirection.DESC

    @override
    def to_query_order(self) -> QueryOrder:
        """Convert to repository QueryOrder."""
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case AccessTokenOrderField.CREATED_AT:
                return AccessTokenOrders.created_at(ascending)


@strawberry.type
class AccessToken(Node):
    id: NodeID[str]
    token: str = strawberry.field(description="Added in 25.16.0: The access token.")
    created_at: datetime = strawberry.field(
        description="Added in 25.16.0: The creation timestamp of the access token."
    )
    valid_until: datetime = strawberry.field(
        description="Added in 25.16.0: The expiration timestamp of the access token."
    )

    @classmethod
    def from_dataclass(cls, data: ModelDeploymentAccessTokenData) -> Self:
        return cls(
            id=ID(str(data.id)),
            token=data.token,
            created_at=data.created_at,
            valid_until=data.valid_until,
        )


AccessTokenEdge = Edge[AccessToken]


@strawberry.type(description="Added in 25.16.0")
class AccessTokenConnection(Connection[AccessToken]):
    count: int

    def __init__(self, *args, count: int, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@strawberry.input
class CreateAccessTokenInput:
    model_deployment_id: ID = strawberry.field(
        description="Added in 25.16.0: The ID of the model deployment for which the access token is created."
    )
    valid_until: datetime = strawberry.field(
        description="Added in 25.16.0: The expiration timestamp of the access token."
    )

    def to_creator(self) -> ModelDeploymentAccessTokenCreator:
        return ModelDeploymentAccessTokenCreator(
            model_deployment_id=UUID(self.model_deployment_id),
            valid_until=self.valid_until,
        )


@strawberry.type
class CreateAccessTokenPayload:
    access_token: AccessToken
