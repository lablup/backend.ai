"""SSH key GraphQL mutation resolvers."""

from __future__ import annotations

from uuid import UUID

from strawberry import Info

from ai.backend.common.data.entity.ssh_keypair import SSHKeypairID
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_mutation
from ai.backend.manager.api.gql.ssh_key.types import MyUploadSSHKeyInputGQL, SSHKeyGQL
from ai.backend.manager.api.gql.types import StrawberryGQLContext


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
