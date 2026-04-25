"""AppConfigPolicy bulk-mutation GQL input types (BEP-1052 §3)."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.app_config_policy.request import (
    AdminAppConfigPolicyItemInput as AdminItemInputDTO,
)
from ai.backend.common.dto.manager.v2.app_config_policy.request import (
    AdminBulkCreateAppConfigPoliciesInput as AdminBulkCreateInputDTO,
)
from ai.backend.common.dto.manager.v2.app_config_policy.request import (
    AdminBulkPurgeAppConfigPoliciesInput as AdminBulkPurgeInputDTO,
)
from ai.backend.common.dto.manager.v2.app_config_policy.request import (
    AdminBulkUpdateAppConfigPoliciesInput as AdminBulkUpdateInputDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Per-item input for admin bulk create / update.",
    ),
    name="AdminAppConfigPolicyItemInput",
)
class AdminAppConfigPolicyItemInputGQL(PydanticInputMixin[AdminItemInputDTO]):
    config_name: str = gql_field(description="Unique, immutable policy name.")
    scope_sources: list[str] = gql_field(description="Ordered scope chain.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Admin bulk create input for app-config policies.",
    ),
    name="AdminBulkCreateAppConfigPolicyInput",
)
class AdminBulkCreateAppConfigPolicyInputGQL(PydanticInputMixin[AdminBulkCreateInputDTO]):
    items: list[AdminAppConfigPolicyItemInputGQL] = gql_field(description="Policies to create.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Admin bulk update input for app-config policies.",
    ),
    name="AdminBulkUpdateAppConfigPolicyInput",
)
class AdminBulkUpdateAppConfigPolicyInputGQL(PydanticInputMixin[AdminBulkUpdateInputDTO]):
    items: list[AdminAppConfigPolicyItemInputGQL] = gql_field(description="Policies to update.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Admin bulk purge input for app-config policies (keyed on `config_name`).",
    ),
    name="AdminBulkPurgeAppConfigPolicyInput",
)
class AdminBulkPurgeAppConfigPolicyInputGQL(PydanticInputMixin[AdminBulkPurgeInputDTO]):
    config_names: list[str] = gql_field(description="`config_name`s to purge.")
