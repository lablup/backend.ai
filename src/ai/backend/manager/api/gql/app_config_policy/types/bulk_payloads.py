"""AppConfigPolicy bulk-mutation GQL payload types."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.app_config_policy.response import (
    AdminBulkCreateAppConfigPoliciesPayload as AdminBulkCreatePayloadDTO,
)
from ai.backend.common.dto.manager.v2.app_config_policy.response import (
    AdminBulkPurgeAppConfigPoliciesPayload as AdminBulkPurgePayloadDTO,
)
from ai.backend.common.dto.manager.v2.app_config_policy.response import (
    AdminBulkUpdateAppConfigPoliciesPayload as AdminBulkUpdatePayloadDTO,
)
from ai.backend.common.dto.manager.v2.app_config_policy.response import (
    AppConfigPolicyBulkError as AppConfigPolicyBulkErrorDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.app_config_policy.types.node import AppConfigPolicyGQL
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticOutputMixin


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Per-item failure info for bulk Policy mutations.",
    ),
    model=AppConfigPolicyBulkErrorDTO,
    name="AppConfigPolicyBulkError",
)
class AppConfigPolicyBulkErrorGQL(PydanticOutputMixin[AppConfigPolicyBulkErrorDTO]):
    index: int = gql_field(description="Original position in the input list.")
    config_name: str = gql_field(description="`config_name` of the failed row.")
    message: str = gql_field(description="Reason for the failure.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for `adminBulkCreateAppConfigPolicies`.",
    ),
    model=AdminBulkCreatePayloadDTO,
    name="AdminBulkCreateAppConfigPoliciesPayload",
)
class AdminBulkCreateAppConfigPoliciesPayloadGQL(PydanticOutputMixin[AdminBulkCreatePayloadDTO]):
    created: list[AppConfigPolicyGQL] = gql_field(description="Created policies.")
    failed: list[AppConfigPolicyBulkErrorGQL] = gql_field(description="Per-item failures.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for `adminBulkUpdateAppConfigPolicies`.",
    ),
    model=AdminBulkUpdatePayloadDTO,
    name="AdminBulkUpdateAppConfigPoliciesPayload",
)
class AdminBulkUpdateAppConfigPoliciesPayloadGQL(PydanticOutputMixin[AdminBulkUpdatePayloadDTO]):
    updated: list[AppConfigPolicyGQL] = gql_field(description="Updated policies.")
    failed: list[AppConfigPolicyBulkErrorGQL] = gql_field(description="Per-item failures.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for `adminBulkPurgeAppConfigPolicies`.",
    ),
    model=AdminBulkPurgePayloadDTO,
    name="AdminBulkPurgeAppConfigPoliciesPayload",
)
class AdminBulkPurgeAppConfigPoliciesPayloadGQL(PydanticOutputMixin[AdminBulkPurgePayloadDTO]):
    purged_config_names: list[str] = gql_field(
        description="`config_name`s of policies actually removed (absent names no-oped).",
    )
    failed: list[AppConfigPolicyBulkErrorGQL] = gql_field(description="Per-item failures.")
