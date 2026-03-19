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
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_node_type


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Payload returned after issuing a new keypair. The secret_key is only shown once.",
    ),
    name="IssueMyKeypairPayload",
)
class IssueMyKeypairPayloadGQL:
    """Payload returned after issuing a new keypair."""

    access_key: str = strawberry.field(description="The newly generated access key.")
    secret_key: str = strawberry.field(
        description="The newly generated secret key. This value is only returned at creation time."
    )
    ssh_public_key: str = strawberry.field(description="The generated SSH public key.")

    @classmethod
    def from_pydantic(cls, dto: IssueMyKeypairPayloadDTO) -> IssueMyKeypairPayloadGQL:
        return cls(
            access_key=dto.access_key,
            secret_key=dto.secret_key,
            ssh_public_key=dto.ssh_public_key,
        )


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Payload returned after revoking a keypair.",
    ),
    name="RevokeMyKeypairPayload",
)
class RevokeMyKeypairPayloadGQL:
    """Payload returned after revoking a keypair."""

    success: bool = strawberry.field(description="Whether the revocation was successful.")

    @classmethod
    def from_pydantic(cls, dto: RevokeMyKeypairPayloadDTO) -> RevokeMyKeypairPayloadGQL:
        return cls(success=dto.success)


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Payload returned after switching the main access key.",
    ),
    name="SwitchMyMainAccessKeyPayload",
)
class SwitchMyMainAccessKeyPayloadGQL:
    """Payload returned after switching the main access key."""

    success: bool = strawberry.field(description="Whether the switch was successful.")

    @classmethod
    def from_pydantic(cls, dto: SwitchMyMainAccessKeyPayloadDTO) -> SwitchMyMainAccessKeyPayloadGQL:
        return cls(success=dto.success)


@strawberry.type(
    name="UpdateMyKeypairPayload",
    description="Payload returned after updating a keypair.",
)
class UpdateMyKeypairPayloadGQL:
    success: bool = strawberry.field(description="Whether the update was successful.")
