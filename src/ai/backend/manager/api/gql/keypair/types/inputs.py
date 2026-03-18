"""Keypair GraphQL mutation input types."""

from __future__ import annotations

import strawberry

from ai.backend.common.dto.manager.v2.auth.request import (
    RevokeMyKeypairInput as RevokeMyKeypairInputDTO,
)
from ai.backend.common.dto.manager.v2.auth.request import (
    SwitchMyMainAccessKeyInput as SwitchMyMainAccessKeyInputDTO,
)


@strawberry.experimental.pydantic.input(
    model=RevokeMyKeypairInputDTO,
    name="RevokeMyKeypairInput",
    description="Input for revoking a keypair owned by the current user.",
)
class RevokeMyKeypairInputGQL:
    access_key: str = strawberry.field(
        description="Access key of the keypair to revoke. Must not be the main access key."
    )


@strawberry.experimental.pydantic.input(
    model=SwitchMyMainAccessKeyInputDTO,
    name="SwitchMyMainAccessKeyInput",
    description="Input for switching the main access key of the current user.",
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
