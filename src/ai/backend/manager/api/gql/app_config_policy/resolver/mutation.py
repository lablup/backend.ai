"""AppConfigPolicy GQL mutation resolvers (bulk-only)."""

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
    """Bulk-create app-config policies; failures surface per-item via `failed`."""
    check_admin_only()
    result = await info.context.adapters.app_config_policy.admin_bulk_create(input.to_pydantic())
    return AdminBulkCreateAppConfigPoliciesPayloadGQL.from_pydantic(result)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Replace `scope_sources`; `config_name` is immutable. Admin only, per-item transaction."
        ),
    )
)
async def admin_bulk_update_app_config_policies(
    info: Info[StrawberryGQLContext],
    input: AdminBulkUpdateAppConfigPolicyInputGQL,
) -> AdminBulkUpdateAppConfigPoliciesPayloadGQL:
    """Bulk-replace `scope_sources` per row id; missing-id items surface in `failed`."""
    check_admin_only()
    result = await info.context.adapters.app_config_policy.admin_bulk_update(input.to_pydantic())
    return AdminBulkUpdateAppConfigPoliciesPayloadGQL.from_pydantic(result)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Hard-delete policies by row id; rows still referenced by fragments surface in `failed`. Admin only."
        ),
    )
)
async def admin_bulk_purge_app_config_policies(
    info: Info[StrawberryGQLContext],
    input: AdminBulkPurgeAppConfigPolicyInputGQL,
) -> AdminBulkPurgeAppConfigPoliciesPayloadGQL:
    """Bulk-purge app-config policies by row id; absent ids no-op."""
    check_admin_only()
    result = await info.context.adapters.app_config_policy.admin_bulk_purge(input.to_pydantic())
    return AdminBulkPurgeAppConfigPoliciesPayloadGQL.from_pydantic(result)
