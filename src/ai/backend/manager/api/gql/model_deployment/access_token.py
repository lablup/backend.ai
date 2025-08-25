from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID

import strawberry
from strawberry import Info
from strawberry.relay import Connection, Edge, Node, NodeID, PageInfo
from strawberry.relay.types import NodeIterableType


@strawberry.type
class AccessToken(Node):
    id: NodeID  # Inherits from Node, no need for strawberry.field()
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
    @strawberry.field
    def count(self) -> int:
        return 0

    @classmethod
    def resolve_connection(
        cls,
        nodes: NodeIterableType[AccessToken],
        *,
        info: Optional[Info] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        last: Optional[int] = None,
        max_results: Optional[int] = None,
        **kwargs: Any,
    ):
        """Resolve the connection for Relay pagination."""
        return cls(
            edges=[],
            page_info=PageInfo(
                has_next_page=False, has_previous_page=False, start_cursor=None, end_cursor=None
            ),
        )


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
