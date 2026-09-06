"""Secret GraphQL payload types."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.secret.response import (
    AdminReencryptSecretsPayload as AdminReencryptSecretsPayloadDTO,
)
from ai.backend.common.dto.manager.v2.secret.response import (
    AdminSecretStatusPayload as AdminSecretStatusPayloadDTO,
)
from ai.backend.common.dto.manager.v2.secret.response import (
    SecretKeyCount as SecretKeyCountDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticOutputMixin


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="How many stored secrets of one column one provider's one key holds.",
    ),
    model=SecretKeyCountDTO,
    name="SecretKeyCount",
)
class SecretKeyCountGQL(PydanticOutputMixin[SecretKeyCountDTO]):
    column: str = gql_field(description="The encrypted column these secrets are stored in.")
    provider_type: str = gql_field(
        description="The key provider holding these secrets. 'plain' means legacy plaintext."
    )
    key_id: str | None = gql_field(description="The key within that provider. Unset for plaintext.")
    count: int = gql_field(description="How many stored secrets that key holds.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Which key each stored secret sits on, across every encrypted column.",
    ),
    model=AdminSecretStatusPayloadDTO,
    name="AdminSecretStatusPayload",
)
class AdminSecretStatusPayloadGQL(PydanticOutputMixin[AdminSecretStatusPayloadDTO]):
    write_provider_type: str = gql_field(
        description="The key provider new and re-encrypted secrets are written through."
    )
    counts: list[SecretKeyCountGQL] = gql_field(
        description="The stored secrets, grouped by column and by the key holding them."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="What one re-encryption pass wrote, and what the columns hold afterwards.",
    ),
    model=AdminReencryptSecretsPayloadDTO,
    name="AdminReencryptSecretsPayload",
)
class AdminReencryptSecretsPayloadGQL(PydanticOutputMixin[AdminReencryptSecretsPayloadDTO]):
    scanned: int = gql_field(description="How many rows this pass read.")
    reencrypted: int = gql_field(description="How many rows this pass wrote back.")
    status: AdminSecretStatusPayloadGQL = gql_field(
        description="The count per column and key id after this pass."
    )
