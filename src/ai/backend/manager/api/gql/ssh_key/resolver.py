"""SSH key GraphQL query and mutation resolvers."""

from __future__ import annotations

from uuid import UUID

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.entity.ssh_keypair import SSHKeypairID
from ai.backend.common.dto.manager.v2.ssh_key.request import (
    ScopedSearchSSHKeysInput,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_mutation, gql_root_field
from ai.backend.manager.api.gql.ssh_key.types import (
    MyUploadSSHKeyInputGQL,
    SSHKeyConnectionGQL,
    SSHKeyEdgeGQL,
    SSHKeyFilterGQL,
    SSHKeyGQL,
    SSHKeyOrderByGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.errors.auth import InsufficientPrivilege


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Read one SSH key. The caller needs read permission on its owner.",
    )
)
async def ssh_key(info: Info[StrawberryGQLContext], id: UUID) -> SSHKeyGQL | None:
    node = await info.context.adapters.ssh_key.get(SSHKeypairID(id))
    return SSHKeyGQL.from_pydantic(node)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Page through the current user's own SSH keys.",
    )
)
async def my_ssh_keys(
    info: Info[StrawberryGQLContext],
    filter: SSHKeyFilterGQL | None = None,
    order_by: list[SSHKeyOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> SSHKeyConnectionGQL | None:
    me = current_user()
    if me is None:
        raise InsufficientPrivilege("Authentication required")
    payload = await info.context.adapters.ssh_key.scoped_search(
        ScopedSearchSSHKeysInput(
            user_id=me.user_id,
            filter=filter.to_pydantic() if filter else None,
            order=[o.to_pydantic() for o in order_by] if order_by else None,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )
    edges = [
        SSHKeyEdgeGQL(node=node, cursor=encode_cursor(str(node.id)))
        for node in (SSHKeyGQL.from_pydantic(item) for item in payload.items)
    ]
    return SSHKeyConnectionGQL(
        edges=edges,
        page_info=PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Upload a public key to the current user's SSH keys. It becomes the default only "
            "when the user has no default yet."
        ),
    )
)
async def my_upload_ssh_key(
    info: Info[StrawberryGQLContext],
    input: MyUploadSSHKeyInputGQL,
) -> SSHKeyGQL | None:
    node = await info.context.adapters.ssh_key.my_upload(input.to_pydantic())
    return SSHKeyGQL.from_pydantic(node)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Make an SSH key the default of its owner, unmarking the previous default. The "
            "caller needs read and update permission on the owner."
        ),
    )
)
async def switch_default_ssh_key(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> SSHKeyGQL | None:
    node = await info.context.adapters.ssh_key.switch_default(SSHKeypairID(id))
    return SSHKeyGQL.from_pydantic(node)
