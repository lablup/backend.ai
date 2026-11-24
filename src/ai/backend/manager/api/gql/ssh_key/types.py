"""SSH key GraphQL types."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Self, cast, override
from uuid import UUID

from strawberry import Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.data.entity.ssh_keypair import SSHKeypairID
from ai.backend.common.dto.manager.v2.ssh_key.request import (
    MyUploadSSHKeyInput,
    SSHKeyFilter,
    SSHKeyOrder,
    SSHKeyOrderField,
)
from ai.backend.common.dto.manager.v2.ssh_key.response import SSHKeyNode
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import OrderDirection
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_connection_type,
    gql_enum,
    gql_field,
    gql_node_type,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="An SSH public key of a user. Sessions use the user's default key.",
    ),
    name="SSHKey",
)
class SSHKeyGQL(PydanticNodeMixin[SSHKeyNode]):
    id: NodeID[str] = gql_field(description="Relay-style global node identifier.")
    field_id: UUID = gql_field(description="UUID of the SSH key.")
    user_id: UUID = gql_field(description="ID of the user the SSH key belongs to.")
    public_key: str = gql_field(description="The SSH public key.")
    is_default: bool = gql_field(description="Whether sessions use this SSH key.")

    @classmethod
    @override
    async def resolve_nodes(
        cls,
        *,
        info: Info[StrawberryGQLContext, Any],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self]:
        results = await info.context.data_loaders.ssh_key_loader.load_many([
            SSHKeypairID(UUID(node_id)) for node_id in node_ids
        ])
        return cast(list[Self], results)


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="A public key the caller uploads to their own SSH keys.",
    ),
    name="MyUploadSSHKeyInput",
)
class MyUploadSSHKeyInputGQL(PydanticInputMixin[MyUploadSSHKeyInput]):
    public_key: str = gql_field(
        description=(
            "The SSH public key in the OpenSSH single-line format. It becomes the default "
            "only when the caller has no default yet."
        )
    )


SSHKeyEdgeGQL = Edge[SSHKeyGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Paginated connection for SSH keys.",
    ),
    name="SSHKeyConnection",
)
class SSHKeyConnectionGQL(Connection[SSHKeyGQL]):
    count: int = gql_field(description="Total number of SSH keys matching the query.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@gql_pydantic_input(
    BackendAIGQLMeta(added_version=NEXT_RELEASE_VERSION, description="Filter for SSH keys."),
    name="SSHKeyFilter",
)
class SSHKeyFilterGQL(PydanticInputMixin[SSHKeyFilter]):
    is_default: bool | None = gql_field(
        description="Filter by whether sessions use the SSH key.", default=None
    )


# gql_enum marks SSHKeyOrderField itself as the GQL enum, so fields annotate the DTO enum.
gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Fields available for ordering SSH keys.",
    ),
    SSHKeyOrderField,
    name="SSHKeyOrderField",
)


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION, description="Order specification for SSH keys."
    ),
    name="SSHKeyOrderBy",
)
class SSHKeyOrderByGQL(PydanticInputMixin[SSHKeyOrder]):
    field: SSHKeyOrderField = gql_field(description="Field to order by.")
    direction: OrderDirection = gql_field(
        description="Order direction.", default=OrderDirection.ASC
    )
