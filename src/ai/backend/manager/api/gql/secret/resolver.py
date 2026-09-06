"""Secret GraphQL resolvers."""

from __future__ import annotations

from strawberry import Info

from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
    gql_root_field,
)
from ai.backend.manager.api.gql.secret.types import (
    AdminReencryptSecretsPayloadGQL,
    AdminSecretStatusPayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Report the stored secrets of every encrypted column per key id (admin only). "
            "Requires superadmin privileges."
        ),
    )
)  # type: ignore[misc]
async def admin_secret_status(
    info: Info[StrawberryGQLContext],
) -> AdminSecretStatusPayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.secret.admin_secret_status()
    return AdminSecretStatusPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Admin encrypts every stored secret again through the configured write provider, "
            "under a fresh data encryption key. The pass runs in chunks and reports the count "
            "per column and key id afterwards."
        ),
    )
)
async def admin_reencrypt_secrets(
    info: Info[StrawberryGQLContext],
) -> AdminReencryptSecretsPayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.secret.admin_reencrypt_secrets()
    return AdminReencryptSecretsPayloadGQL.from_pydantic(payload)
