"""AppConfigFragment bulk-mutation GQL input types."""

from __future__ import annotations

from strawberry.scalars import JSON

from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    AdminAppConfigFragmentItemInput as AdminItemInputDTO,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    AdminBulkCreateAppConfigFragmentsInput as AdminBulkCreateInputDTO,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    AdminBulkPurgeAppConfigFragmentsInput as AdminBulkPurgeInputDTO,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    AdminBulkUpdateAppConfigFragmentsInput as AdminBulkUpdateInputDTO,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    MyAppConfigFragmentItemInput as MyItemInputDTO,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    MyBulkCreateAppConfigFragmentsInput as MyBulkCreateInputDTO,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    MyBulkUpdateAppConfigFragmentsInput as MyBulkUpdateInputDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.app_config_fragment.types.inputs import (
    AppConfigFragmentKeyInputGQL,
)
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
    name="AdminAppConfigFragmentItemInput",
)
class AdminAppConfigFragmentItemInputGQL(PydanticInputMixin[AdminItemInputDTO]):
    key: AppConfigFragmentKeyInputGQL = gql_field(description="Natural-key identifier.")
    config: JSON = gql_field(description="Raw configuration payload.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Admin bulk create input — items carry any scope.",
    ),
    name="AdminBulkCreateAppConfigFragmentInput",
)
class AdminBulkCreateAppConfigFragmentInputGQL(PydanticInputMixin[AdminBulkCreateInputDTO]):
    items: list[AdminAppConfigFragmentItemInputGQL] = gql_field(description="Rows to create.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Admin bulk update input.",
    ),
    name="AdminBulkUpdateAppConfigFragmentInput",
)
class AdminBulkUpdateAppConfigFragmentInputGQL(PydanticInputMixin[AdminBulkUpdateInputDTO]):
    items: list[AdminAppConfigFragmentItemInputGQL] = gql_field(description="Rows to update.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Admin bulk purge input — keyed on `AppConfigFragmentKey`.",
    ),
    name="AdminBulkPurgeAppConfigFragmentInput",
)
class AdminBulkPurgeAppConfigFragmentInputGQL(PydanticInputMixin[AdminBulkPurgeInputDTO]):
    keys: list[AppConfigFragmentKeyInputGQL] = gql_field(description="Natural keys to purge.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Per-item input for self-service (`my`) bulk.",
    ),
    name="MyAppConfigFragmentItemInput",
)
class MyAppConfigFragmentItemInputGQL(PydanticInputMixin[MyItemInputDTO]):
    name: str = gql_field(description="Policy name.")
    config: JSON = gql_field(description="Raw configuration payload.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Self-service bulk create — scope is `USER` / `current_user`.",
    ),
    name="MyBulkCreateAppConfigFragmentInput",
)
class MyBulkCreateAppConfigFragmentInputGQL(PydanticInputMixin[MyBulkCreateInputDTO]):
    items: list[MyAppConfigFragmentItemInputGQL] = gql_field(
        description="USER-scope rows to create.",
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Self-service bulk update — scope is `USER` / `current_user`.",
    ),
    name="MyBulkUpdateAppConfigFragmentInput",
)
class MyBulkUpdateAppConfigFragmentInputGQL(PydanticInputMixin[MyBulkUpdateInputDTO]):
    items: list[MyAppConfigFragmentItemInputGQL] = gql_field(
        description="USER-scope rows to update.",
    )
