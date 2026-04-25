"""AppConfigPolicy GQL mutation resolvers (bulk-only, BEP-1052 §3)."""

from __future__ import annotations

from strawberry import Info

from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.app_config_policy.types import (
    AdminBulkCreateAppConfigPoliciesPayloadGQL,
    AdminBulkCreateAppConfigPolicyInputGQL,
    AdminBulkPurgeAppConfigPoliciesPayloadGQL,
    AdminBulkPurgeAppConfigPolicyInputGQL,
    AdminBulkUpdateAppConfigPoliciesPayloadGQL,
    AdminBulkUpdateAppConfigPolicyInputGQL,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Strict insert keyed on `configName` (admin only, per-item transaction).",
    )
)
async def admin_bulk_create_app_config_policies(
    info: Info[StrawberryGQLContext],
    input: AdminBulkCreateAppConfigPolicyInputGQL,
) -> AdminBulkCreateAppConfigPoliciesPayloadGQL:
    check_admin_only()
    result = await info.context.adapters.app_config_policy.admin_bulk_create(input.to_pydantic())
    return AdminBulkCreateAppConfigPoliciesPayloadGQL.from_pydantic(result)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Replace `scope_sources`; `config_name` is immutable (BEP-1052 §1). "
            "Admin only, per-item transaction."
        ),
    )
)
async def admin_bulk_update_app_config_policies(
    info: Info[StrawberryGQLContext],
    input: AdminBulkUpdateAppConfigPolicyInputGQL,
) -> AdminBulkUpdateAppConfigPoliciesPayloadGQL:
    check_admin_only()
    result = await info.context.adapters.app_config_policy.admin_bulk_update(input.to_pydantic())
    return AdminBulkUpdateAppConfigPoliciesPayloadGQL.from_pydantic(result)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Rejects items whose `config_name` still has referencing fragment rows "
            "(BEP-1052 §1). Admin only."
        ),
    )
)
async def admin_bulk_purge_app_config_policies(
    info: Info[StrawberryGQLContext],
    input: AdminBulkPurgeAppConfigPolicyInputGQL,
) -> AdminBulkPurgeAppConfigPoliciesPayloadGQL:
    check_admin_only()
    result = await info.context.adapters.app_config_policy.admin_bulk_purge(input.to_pydantic())
    return AdminBulkPurgeAppConfigPoliciesPayloadGQL.from_pydantic(result)
