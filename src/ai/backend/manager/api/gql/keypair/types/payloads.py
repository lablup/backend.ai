"""Keypair GraphQL mutation payload types."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.keypair.response import (
    AdminCreateKeypairPayload as AdminCreateKeypairPayloadDTO,
)
from ai.backend.common.dto.manager.v2.keypair.response import (
    AdminDeleteKeypairPayload as AdminDeleteKeypairPayloadDTO,
)
from ai.backend.common.dto.manager.v2.keypair.response import (
    AdminUpdateKeypairPayload as AdminUpdateKeypairPayloadDTO,
)
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
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.keypair.types.node import KeyPairGQL
from ai.backend.manager.api.gql.pydantic_compat import PydanticOutputMixin


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Payload returned after issuing a new keypair. The secret_key is only shown once.",
    ),
    model=IssueMyKeypairPayloadDTO,
    fields=["secret_key"],
    name="IssueMyKeypairPayload",
)
class IssueMyKeypairPayloadGQL(PydanticOutputMixin[IssueMyKeypairPayloadDTO]):
    keypair: KeyPairGQL = gql_field(description="The newly created keypair.")


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
    fields=[],
    name="UpdateMyKeypairPayload",
)
class UpdateMyKeypairPayloadGQL(PydanticOutputMixin[UpdateMyKeypairPayloadDTO]):
    keypair: KeyPairGQL = gql_field(description="The updated keypair.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload returned after admin creates a keypair. The secret_key is only shown once.",
    ),
    model=AdminCreateKeypairPayloadDTO,
    fields=["secret_key"],
    name="AdminCreateKeypairPayload",
)
class AdminCreateKeypairPayloadGQL(PydanticOutputMixin[AdminCreateKeypairPayloadDTO]):
    keypair: KeyPairGQL = gql_field(description="The newly created keypair.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload returned after admin updates a keypair.",
    ),
    model=AdminUpdateKeypairPayloadDTO,
    fields=[],
    name="AdminUpdateKeypairPayload",
)
class AdminUpdateKeypairPayloadGQL(PydanticOutputMixin[AdminUpdateKeypairPayloadDTO]):
    keypair: KeyPairGQL = gql_field(description="The updated keypair.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload returned after admin deletes a keypair.",
    ),
    model=AdminDeleteKeypairPayloadDTO,
    all_fields=True,
    name="AdminDeleteKeypairPayload",
)
class AdminDeleteKeypairPayloadGQL(PydanticOutputMixin[AdminDeleteKeypairPayloadDTO]):
    pass
