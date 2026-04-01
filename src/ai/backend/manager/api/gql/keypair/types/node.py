"""Keypair GraphQL Node, Edge, and Connection types."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.keypair.response import KeypairNode
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_connection_type,
    gql_field,
    gql_node_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Keypair entity representing an API access key. "
            "The access_key field serves as the unique identifier. "
            "Secret key and private SSH key are excluded for security reasons."
        ),
    ),
    name="KeyPairGQL",
)
class KeyPairGQL(PydanticNodeMixin[KeypairNode]):
    """Keypair entity accessible via Relay Node interface."""

    id: NodeID[str] = gql_field(description="Access key (primary key, used as the Relay Node ID).")
    access_key: str = gql_field(description="The access key string.")
    is_active: bool | None = gql_field(description="Whether the keypair is currently active.")
    is_admin: bool | None = gql_field(description="Whether the keypair has admin privileges.")
    created_at: datetime | None = gql_field(description="Timestamp when the keypair was created.")
    modified_at: datetime | None = gql_field(
        description="Timestamp when the keypair was last modified."
    )
    last_used: datetime | None = gql_field(
        description="Timestamp when the keypair was last used for an API call."
    )
    rate_limit: int = gql_field(description="API rate limit (requests per minute).")
    num_queries: int = gql_field(description="Total number of API queries made with this keypair.")
    resource_policy: str = gql_field(
        description="Name of the resource policy assigned to this keypair."
    )
    ssh_public_key: str | None = gql_field(
        description="The SSH public key associated with this keypair."
    )
    user_id: UUID = gql_field(description="UUID of the user who owns this keypair.")


KeyPairEdge = Edge[KeyPairGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Paginated connection for keypair records. "
            "Provides relay-style cursor-based pagination. "
            "Use 'edges' to access individual records with cursor information."
        ),
    )
)
class KeyPairConnection(Connection[KeyPairGQL]):
    """Paginated connection for keypair records."""

    count: int = gql_field(
        description="Total number of keypair records matching the query criteria."
    )

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
