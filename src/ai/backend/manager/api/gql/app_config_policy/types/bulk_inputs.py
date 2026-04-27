"""AppConfigPolicy bulk-mutation GQL input types."""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.dto.manager.v2.app_config_policy.request import (
    AdminAppConfigPolicyCreateItemInput as AdminCreateItemInputDTO,
)
from ai.backend.common.dto.manager.v2.app_config_policy.request import (
    AdminAppConfigPolicyUpdateItemInput as AdminUpdateItemInputDTO,
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
        description="Per-item input for admin bulk create — `config_name` + initial `scope_sources`.",
    ),
    name="AdminAppConfigPolicyCreateItemInput",
)
class AdminAppConfigPolicyCreateItemInputGQL(PydanticInputMixin[AdminCreateItemInputDTO]):
    config_name: str = gql_field(description="Unique, immutable policy name.")
    scope_sources: list[str] = gql_field(description="Ordered scope chain.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Per-item input for admin bulk update — target row id + new `scope_sources`.",
    ),
    name="AdminAppConfigPolicyUpdateItemInput",
)
class AdminAppConfigPolicyUpdateItemInputGQL(PydanticInputMixin[AdminUpdateItemInputDTO]):
    id: UUID = gql_field(description="Policy row id.")
    scope_sources: list[str] = gql_field(description="Ordered scope chain.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Admin bulk create input for app-config policies.",
    ),
    name="AdminBulkCreateAppConfigPolicyInput",
)
class AdminBulkCreateAppConfigPolicyInputGQL(PydanticInputMixin[AdminBulkCreateInputDTO]):
    items: list[AdminAppConfigPolicyCreateItemInputGQL] = gql_field(
        description="Policies to create."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Admin bulk update input for app-config policies.",
    ),
    name="AdminBulkUpdateAppConfigPolicyInput",
)
class AdminBulkUpdateAppConfigPolicyInputGQL(PydanticInputMixin[AdminBulkUpdateInputDTO]):
    items: list[AdminAppConfigPolicyUpdateItemInputGQL] = gql_field(
        description="Policies to update."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Admin bulk purge input for app-config policies (keyed on row id).",
    ),
    name="AdminBulkPurgeAppConfigPolicyInput",
)
class AdminBulkPurgeAppConfigPolicyInputGQL(PydanticInputMixin[AdminBulkPurgeInputDTO]):
    ids: list[UUID] = gql_field(description="Policy row ids to purge.")
