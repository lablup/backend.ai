"""Role preset GQL filter and order-by types."""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from ai.backend.common.dto.manager.v2.role_preset.request import (
    RolePresetFilter as RolePresetFilterDTO,
)
from ai.backend.common.dto.manager.v2.role_preset.request import (
    RolePresetOrder as RolePresetOrderDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_enum,
    gql_field,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin
from ai.backend.manager.api.gql.rbac.types import RBACElementTypeFilterGQL


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter input for querying role presets.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="RolePresetFilter",
)
class RolePresetFilterGQL(PydanticInputMixin[RolePresetFilterDTO]):
    name: StringFilter | None = gql_field(description="Filter by name.", default=None)
    scope_type: RBACElementTypeFilterGQL | None = gql_field(
        description="Filter by scope type.", default=None
    )
    auto_assign: bool | None = gql_field(description="Filter by auto-assign flag.", default=None)
    deleted: bool | None = gql_field(
        description=(
            "Filter by soft-delete flag. Searches exclude soft-deleted rows by default; "
            "set this explicitly to `true` to inspect archived presets."
        ),
        default=None,
    )
    AND: list[Self] | None = gql_field(
        description="Combine multiple filters with AND logic. All conditions must match.",
        default=None,
    )
    OR: list[Self] | None = gql_field(
        description="Combine multiple filters with OR logic. At least one condition must match.",
        default=None,
    )
    NOT: list[Self] | None = gql_field(
        description="Negate the specified filters. Matching records are excluded.",
        default=None,
    )


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Fields available for ordering role preset results.",
    ),
    name="RolePresetOrderField",
)
class RolePresetOrderFieldGQL(StrEnum):
    NAME = "name"
    SCOPE_TYPE = "scope_type"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Specifies ordering for role preset results.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="RolePresetOrderBy",
)
class RolePresetOrderByGQL(PydanticInputMixin[RolePresetOrderDTO]):
    field: RolePresetOrderFieldGQL = gql_field(description="The field to order by.")
    direction: OrderDirection = gql_field(description="Sort direction.", default=OrderDirection.ASC)
