"""Keypair GraphQL mutation payload types."""

from __future__ import annotations

import strawberry


@strawberry.type(
    name="IssueMyKeypairPayload",
    description="Payload returned after issuing a new keypair. The secret_key is only shown once.",
)
class IssueMyKeypairPayloadGQL:
    access_key: str = strawberry.field(description="The newly generated access key.")
    secret_key: str = strawberry.field(
        description="The newly generated secret key. This value is only returned at creation time."
    )
    ssh_public_key: str = strawberry.field(description="The generated SSH public key.")


@strawberry.type(
    name="RevokeMyKeypairPayload",
    description="Payload returned after revoking a keypair.",
)
class RevokeMyKeypairPayloadGQL:
    success: bool = strawberry.field(description="Whether the revocation was successful.")


@strawberry.type(
    name="SwitchMyMainAccessKeyPayload",
    description="Payload returned after switching the main access key.",
)
class SwitchMyMainAccessKeyPayloadGQL:
    success: bool = strawberry.field(description="Whether the switch was successful.")


@strawberry.type(
    name="UpdateMyKeypairPayload",
    description="Payload returned after updating a keypair.",
)
class UpdateMyKeypairPayloadGQL:
    success: bool = strawberry.field(description="Whether the update was successful.")
