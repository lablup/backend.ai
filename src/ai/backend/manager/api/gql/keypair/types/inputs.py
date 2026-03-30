"""Keypair GraphQL mutation input types."""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.dto.manager.v2.keypair.request import (
    AdminCreateKeypairInput as AdminCreateKeypairInputDTO,
)
from ai.backend.common.dto.manager.v2.keypair.request import (
    AdminUpdateKeypairInput as AdminUpdateKeypairInputDTO,
)
from ai.backend.common.dto.manager.v2.keypair.request import (
    RevokeMyKeypairInput as RevokeMyKeypairInputDTO,
)
from ai.backend.common.dto.manager.v2.keypair.request import (
    SwitchMyMainAccessKeyInput as SwitchMyMainAccessKeyInputDTO,
)
from ai.backend.common.dto.manager.v2.keypair.request import (
    UpdateMyKeypairInput as UpdateMyKeypairInputDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
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


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Admin input for creating a keypair for a user.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="AdminCreateKeypairInput",
)
class AdminCreateKeypairInputGQL(PydanticInputMixin[AdminCreateKeypairInputDTO]):
    user_id: UUID = gql_field(description="UUID of the target user.")
    resource_policy: str = gql_field(description="Name of the resource policy to assign.")
    is_active: bool = gql_field(default=True, description="Whether the keypair should be active.")
    is_admin: bool = gql_field(
        default=False, description="Whether the keypair has admin privileges."
    )
    rate_limit: int = gql_field(default=30000, description="API rate limit (requests per minute).")


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Admin input for updating a keypair.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="AdminUpdateKeypairInput",
)
class AdminUpdateKeypairInputGQL(PydanticInputMixin[AdminUpdateKeypairInputDTO]):
    access_key: str = gql_field(description="Access key of the keypair to update.")
    is_active: bool | None = gql_field(default=None, description="New active state.")
    is_admin: bool | None = gql_field(default=None, description="New admin privilege state.")
    resource_policy: str | None = gql_field(default=None, description="New resource policy name.")
    rate_limit: int | None = gql_field(default=None, description="New API rate limit.")
