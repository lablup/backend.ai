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


@strawberry.experimental.pydantic.type(
    model=IssueMyKeypairPayloadDTO,
    name="IssueMyKeypairPayload",
    description="Payload returned after issuing a new keypair. The secret_key is only shown once.",
    all_fields=True,
)
class IssueMyKeypairPayloadGQL:
    """Payload returned after issuing a new keypair."""


@strawberry.experimental.pydantic.type(
    model=RevokeMyKeypairPayloadDTO,
    name="RevokeMyKeypairPayload",
    description="Payload returned after revoking a keypair.",
    all_fields=True,
)
class RevokeMyKeypairPayloadGQL:
    """Payload returned after revoking a keypair."""


@strawberry.experimental.pydantic.type(
    model=SwitchMyMainAccessKeyPayloadDTO,
    name="SwitchMyMainAccessKeyPayload",
    description="Payload returned after switching the main access key.",
    all_fields=True,
)
class SwitchMyMainAccessKeyPayloadGQL:
    """Payload returned after switching the main access key."""


@strawberry.type(
    name="UpdateMyKeypairPayload",
    description="Payload returned after updating a keypair.",
)
class UpdateMyKeypairPayloadGQL:
    success: bool = strawberry.field(description="Whether the update was successful.")
