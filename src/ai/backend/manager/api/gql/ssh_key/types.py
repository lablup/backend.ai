"""SSH key GraphQL types."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Self, override
from uuid import UUID

from strawberry import Info
from strawberry.relay import NodeID

from ai.backend.common.dto.manager.v2.ssh_key.request import MyUploadSSHKeyInput
from ai.backend.common.dto.manager.v2.ssh_key.response import SSHKeyNode
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_field,
    gql_node_type,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.errors.api import NotImplementedAPI


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
    def resolve_nodes(
        cls,
        *,
        info: Info,
        node_ids: Iterable[str],
        required: bool = False,
    ) -> list[Self]:
        raise NotImplementedAPI("SSH key node resolution is not implemented.")


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
