from datetime import datetime, timedelta
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.manager.api.gql.types import StrawberryGQLContext


@strawberry.type
class AccessToken(Node):
    id: NodeID
    token: str = strawberry.field(description="Added in 25.13.0: The access token.")
    created_at: datetime = strawberry.field(
        description="Added in 25.13.0: The creation timestamp of the access token."
    )
    valid_until: datetime = strawberry.field(
        description="Added in 25.13.0: The expiration timestamp of the access token."
    )


AccessTokenEdge = Edge[AccessToken]


@strawberry.type(description="Added in 25.13.0")
class AccessTokenConnection(Connection[AccessToken]):
    count: int

    def __init__(self, *args, count: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.count = count


mock_access_token_1 = AccessToken(
    id=UUID("13cd8325-9307-49e4-94eb-ded2581363f8"),
    token="mock-token-1",
    created_at=datetime.now(),
    valid_until=datetime.now() + timedelta(hours=12),
)

mock_access_token_2 = AccessToken(
    id=UUID("dc1a223a-7437-4e6f-aedf-23417d0486dd"),
    token="mock-token-2",
    created_at=datetime.now(),
    valid_until=datetime.now() + timedelta(hours=1),
)

mock_access_token_3 = AccessToken(
    id=UUID("39f8b49e-0ddf-4dfb-92d6-003c771684b7"),
    token="mock-token-3",
    created_at=datetime.now(),
    valid_until=datetime.now() + timedelta(hours=100),
)

mock_access_token_4 = AccessToken(
    id=UUID("85a6ed1e-133b-4f58-9c06-f667337c6111"),
    token="mock-token-4",
    created_at=datetime.now(),
    valid_until=datetime.now() + timedelta(hours=10),
)

mock_access_token_5 = AccessToken(
    id=UUID("c42f8578-b31d-4203-b858-93f93b4b9549"),
    token="mock-token-5",
    created_at=datetime.now(),
    valid_until=datetime.now() + timedelta(hours=3),
)


@strawberry.input
class CreateAccessTokenInput:
    model_deployment_id: ID = strawberry.field(
        description="Added in 25.13.0: The ID of the model deployment for which the access token is created."
    )
    valid_until: datetime = strawberry.field(
        description="Added in 25.13.0: The expiration timestamp of the access token."
    )


@strawberry.type
class CreateAccessTokenPayload:
    access_token: AccessToken


@strawberry.mutation(description="Added in 25.13.0")
async def create_access_token(
    input: CreateAccessTokenInput, info: Info[StrawberryGQLContext]
) -> CreateAccessTokenPayload:
    return CreateAccessTokenPayload(access_token=mock_access_token_1)
