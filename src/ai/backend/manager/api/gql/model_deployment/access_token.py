from collections.abc import Sequence
from datetime import datetime
from typing import Self
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.common.exception import ModelDeploymentUnavailable
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.data.deployment.access_token import ModelDeploymentAccessTokenCreator
from ai.backend.manager.data.deployment.types import ModelDeploymentAccessTokenData
from ai.backend.manager.services.deployment.actions.access_token.batch_load_by_deployment_ids import (
    BatchLoadAccessTokensByDeploymentIdsAction,
)
from ai.backend.manager.services.deployment.actions.access_token.create_access_token import (
    CreateAccessTokenAction,
)


@strawberry.type
class AccessToken(Node):
    id: NodeID[str]
    token: str = strawberry.field(description="Added in 25.15.0: The access token.")
    created_at: datetime = strawberry.field(
        description="Added in 25.15.0: The creation timestamp of the access token."
    )
    valid_until: datetime = strawberry.field(
        description="Added in 25.15.0: The expiration timestamp of the access token."
    )

    @classmethod
    def from_dataclass(cls, data: ModelDeploymentAccessTokenData) -> Self:
        return cls(
            id=ID(str(data.id)),
            token=data.token,
            created_at=data.created_at,
            valid_until=data.valid_until,
        )

    @classmethod
    async def batch_load_by_deployment_ids(
        cls, ctx: StrawberryGQLContext, deployment_ids: Sequence[UUID]
    ) -> list[list["AccessToken"]]:
        """Batch load access tokens by deployment IDs."""
        processor = ctx.processors.deployment
        if processor is None:
            raise ModelDeploymentUnavailable(
                "Model Deployment feature is unavailable. Please contact support."
            )

        result = await processor.batch_load_access_tokens_by_deployment_ids.wait_for_complete(
            BatchLoadAccessTokensByDeploymentIdsAction(deployment_ids=list(deployment_ids))
        )
        access_tokens = []
        for deployment_id in deployment_ids:
            tokens = result.data.get(deployment_id, [])
            access_tokens.append([AccessToken.from_dataclass(token) for token in tokens])

        return access_tokens


AccessTokenEdge = Edge[AccessToken]


@strawberry.type(description="Added in 25.15.0")
class AccessTokenConnection(Connection[AccessToken]):
    count: int

    def __init__(self, *args, count: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.count = count


@strawberry.input
class CreateAccessTokenInput:
    model_deployment_id: ID = strawberry.field(
        description="Added in 25.15.0: The ID of the model deployment for which the access token is created."
    )
    valid_until: datetime = strawberry.field(
        description="Added in 25.15.0: The expiration timestamp of the access token."
    )

    def to_creator(self) -> "ModelDeploymentAccessTokenCreator":
        return ModelDeploymentAccessTokenCreator(
            model_deployment_id=UUID(self.model_deployment_id),
            valid_until=self.valid_until,
        )


@strawberry.type
class CreateAccessTokenPayload:
    access_token: AccessToken


@strawberry.mutation(description="Added in 25.15.0")
async def create_access_token(
    input: CreateAccessTokenInput, info: Info[StrawberryGQLContext]
) -> CreateAccessTokenPayload:
    deployment_processor = info.context.processors.deployment
    assert deployment_processor is not None
    result = await deployment_processor.create_access_token.wait_for_complete(
        action=CreateAccessTokenAction(input.to_creator())
    )
    return CreateAccessTokenPayload(access_token=AccessToken.from_dataclass(result.data))
