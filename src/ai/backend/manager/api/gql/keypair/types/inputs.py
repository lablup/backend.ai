"""Keypair GraphQL mutation input types."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.keypair.request import (
    RevokeMyKeypairInput as RevokeMyKeypairInputDTO,
)
from ai.backend.common.dto.manager.v2.keypair.request import (
    SwitchMyMainAccessKeyInput as SwitchMyMainAccessKeyInputDTO,
)
from ai.backend.common.dto.manager.v2.keypair.request import (
    UpdateMyKeypairInput as UpdateMyKeypairInputDTO,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_field,
    gql_pydantic_input,
)


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for revoking a keypair owned by the current user.",
        added_version="24.09.0",
    ),
    name="RevokeMyKeypairInput",
)
class RevokeMyKeypairInputGQL(PydanticInputMixin[RevokeMyKeypairInputDTO]):
    access_key: str = gql_field(
        description="Access key of the keypair to revoke. Must not be the main access key."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for switching the main access key of the current user.",
        added_version="24.09.0",
    ),
    name="SwitchMyMainAccessKeyInput",
)
class SwitchMyMainAccessKeyInputGQL(PydanticInputMixin[SwitchMyMainAccessKeyInputDTO]):
    access_key: str = gql_field(
        description="Access key to set as the new main access key. Must be active and owned by the user."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for updating a keypair owned by the current user.",
        added_version="24.09.0",
    ),
    name="UpdateMyKeypairInput",
)
class UpdateMyKeypairInputGQL(PydanticInputMixin[UpdateMyKeypairInputDTO]):
    access_key: str = gql_field(
        description="Access key of the keypair to update. Must be owned by the current user."
    )
    is_active: bool = gql_field(description="Target active state for the keypair.")
