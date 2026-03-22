"""Keypair GraphQL mutation payload types."""

from __future__ import annotations

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
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_pydantic_type
from ai.backend.manager.api.gql.pydantic_compat import PydanticOutputMixin


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Payload returned after issuing a new keypair. The secret_key is only shown once.",
    ),
    model=IssueMyKeypairPayloadDTO,
    all_fields=True,
    name="IssueMyKeypairPayload",
)
class IssueMyKeypairPayloadGQL(PydanticOutputMixin[IssueMyKeypairPayloadDTO]):
    pass


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Payload returned after revoking a keypair.",
    ),
    model=RevokeMyKeypairPayloadDTO,
    all_fields=True,
    name="RevokeMyKeypairPayload",
)
class RevokeMyKeypairPayloadGQL(PydanticOutputMixin[RevokeMyKeypairPayloadDTO]):
    pass


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Payload returned after switching the main access key.",
    ),
    model=SwitchMyMainAccessKeyPayloadDTO,
    all_fields=True,
    name="SwitchMyMainAccessKeyPayload",
)
class SwitchMyMainAccessKeyPayloadGQL(PydanticOutputMixin[SwitchMyMainAccessKeyPayloadDTO]):
    pass


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Payload returned after updating a keypair.",
    ),
    model=UpdateMyKeypairPayloadDTO,
    all_fields=True,
    name="UpdateMyKeypairPayload",
)
class UpdateMyKeypairPayloadGQL(PydanticOutputMixin[UpdateMyKeypairPayloadDTO]):
    pass
