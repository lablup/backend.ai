from datetime import datetime

import strawberry
from strawberry.relay import Node, NodeID


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
