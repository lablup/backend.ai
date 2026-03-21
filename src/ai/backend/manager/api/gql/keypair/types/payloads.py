"""Keypair GraphQL mutation payload types."""

from __future__ import annotations

import strawberry

from ai.backend.common.dto.manager.v2.keypair.response import (
    IssueMyKeypairPayload as IssueMyKeypairPayloadDTO,
)
from ai.backend.common.dto.manager.v2.keypair.response import (
    RevokeMyKeypairPayload as RevokeMyKeypairPayloadDTO,
)
from ai.backend.common.dto.manager.v2.keypair.response import (
    SwitchMyMainAccessKeyPayload as SwitchMyMainAccessKeyPayloadDTO,
)
from ai.backend.common.dto.manager.v2.keypair.response import (
    UpdateMyKeypairPayload as UpdateMyKeypairPayloadDTO,
)
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_from_pydantic_type
from ai.backend.manager.api.gql.pydantic_compat import PydanticOutputMixin


@gql_from_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Payload returned after issuing a new keypair. The secret_key is only shown once.",
    ),
    name="IssueMyKeypairPayload",
)
class IssueMyKeypairPayloadGQL(PydanticOutputMixin[IssueMyKeypairPayloadDTO]):
    """Payload returned after issuing a new keypair."""

    access_key: str = strawberry.field(description="The newly generated access key.")
    secret_key: str = strawberry.field(
        description="The newly generated secret key. This value is only returned at creation time."
    )
    ssh_public_key: str = strawberry.field(description="The generated SSH public key.")


@gql_from_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Payload returned after revoking a keypair.",
    ),
    name="RevokeMyKeypairPayload",
)
class RevokeMyKeypairPayloadGQL(PydanticOutputMixin[RevokeMyKeypairPayloadDTO]):
    """Payload returned after revoking a keypair."""

    success: bool = strawberry.field(description="Whether the revocation was successful.")


@gql_from_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Payload returned after switching the main access key.",
    ),
    name="SwitchMyMainAccessKeyPayload",
)
class SwitchMyMainAccessKeyPayloadGQL(PydanticOutputMixin[SwitchMyMainAccessKeyPayloadDTO]):
    """Payload returned after switching the main access key."""

    success: bool = strawberry.field(description="Whether the switch was successful.")


@gql_from_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Payload returned after updating a keypair.",
    ),
    name="UpdateMyKeypairPayload",
)
class UpdateMyKeypairPayloadGQL(PydanticOutputMixin[UpdateMyKeypairPayloadDTO]):
    success: bool = strawberry.field(description="Whether the update was successful.")
