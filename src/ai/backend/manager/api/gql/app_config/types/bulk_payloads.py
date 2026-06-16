"""AppConfig (merged-view) GQL payloads for self-service bulk mutations."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.app_config.response import (
    MyBulkCreateAppConfigFragmentsPayload as MyBulkCreatePayloadDTO,
)
from ai.backend.common.dto.manager.v2.app_config.response import (
    MyBulkUpdateAppConfigFragmentsPayload as MyBulkUpdatePayloadDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.app_config.types.node import AppConfigGQL
from ai.backend.manager.api.gql.app_config_fragment.types.bulk_payloads import (
    AppConfigFragmentBulkErrorGQL,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticOutputMixin


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for `myBulkCreateAppConfigFragments` (recomputed views).",
    ),
    model=MyBulkCreatePayloadDTO,
    name="MyBulkCreateAppConfigFragmentsPayload",
)
class MyBulkCreateAppConfigFragmentsPayloadGQL(PydanticOutputMixin[MyBulkCreatePayloadDTO]):
    created: list[AppConfigGQL] = gql_field(
        description="Recomputed merged AppConfig views for each created USER fragment.",
    )
    failed: list[AppConfigFragmentBulkErrorGQL] = gql_field(
        description="Per-item failures.",
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for `myBulkUpdateAppConfigFragments` (recomputed views).",
    ),
    model=MyBulkUpdatePayloadDTO,
    name="MyBulkUpdateAppConfigFragmentsPayload",
)
class MyBulkUpdateAppConfigFragmentsPayloadGQL(PydanticOutputMixin[MyBulkUpdatePayloadDTO]):
    updated: list[AppConfigGQL] = gql_field(
        description="Recomputed merged AppConfig views for each updated USER fragment.",
    )
    failed: list[AppConfigFragmentBulkErrorGQL] = gql_field(
        description="Per-item failures.",
    )
