"""Keypair GraphQL mutation input types."""

from __future__ import annotations

import strawberry

from ai.backend.common.dto.manager.v2.auth.request import (
    RevokeMyKeypairInput as RevokeMyKeypairInputDTO,
)
from ai.backend.common.dto.manager.v2.auth.request import (
    SwitchMyMainAccessKeyInput as SwitchMyMainAccessKeyInputDTO,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_pydantic_input,
)


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for revoking a keypair owned by the current user.",
        added_version="24.09.0",
    ),
    model=RevokeMyKeypairInputDTO,
    name="RevokeMyKeypairInput",
)
class RevokeMyKeypairInputGQL:
    access_key: str = strawberry.field(
        description="Access key of the keypair to revoke. Must not be the main access key."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for switching the main access key of the current user.",
        added_version="24.09.0",
    ),
    model=SwitchMyMainAccessKeyInputDTO,
    name="SwitchMyMainAccessKeyInput",
)
class SwitchMyMainAccessKeyInputGQL:
    access_key: str = strawberry.field(
        description="Access key to set as the new main access key. Must be active and owned by the user."
    )


@strawberry.input(
    name="UpdateMyKeypairInput",
    description="Input for updating a keypair owned by the current user.",
)
class UpdateMyKeypairInputGQL:
    access_key: str = strawberry.field(
        description="Access key of the keypair to update. Must be owned by the current user."
    )
    is_active: bool = strawberry.field(description="Target active state for the keypair.")
