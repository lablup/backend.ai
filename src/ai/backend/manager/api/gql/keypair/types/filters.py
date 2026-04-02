"""Keypair GraphQL filter and order-by types."""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from ai.backend.common.dto.manager.v2.keypair.request import KeypairFilter, KeypairOrderBy
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import DateTimeFilter, OrderDirection, StringFilter
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_enum, gql_pydantic_input
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin


@gql_pydantic_input(
    BackendAIGQLMeta(
        description=(
            "Filter input for keypair queries. "
            "Supports filtering by active state, admin flag, and access key. "
            "Multiple filters can be combined using AND, OR, and NOT logical operators."
        ),
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="KeypairFilter",
)
class KeypairFilterGQL(PydanticInputMixin[KeypairFilter]):
    """Filter for keypair queries."""

    is_active: bool | None = None
    is_admin: bool | None = None
    access_key: StringFilter | None = None
    resource_policy: StringFilter | None = None
    created_at: DateTimeFilter | None = None
    last_used: DateTimeFilter | None = None
    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Fields available for ordering keypair query results. "
            "CREATED_AT: Order by creation timestamp. "
            "LAST_USED: Order by last used timestamp. "
            "ACCESS_KEY: Order by access key alphabetically. "
            "IS_ACTIVE: Order by active status."
        ),
    ),
    name="KeypairOrderField",
)
class KeypairOrderFieldGQL(StrEnum):
    CREATED_AT = "created_at"
    LAST_USED = "last_used"
    ACCESS_KEY = "access_key"
    IS_ACTIVE = "is_active"
    RESOURCE_POLICY = "resource_policy"


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Specifies ordering for keypair query results. Default direction is DESC.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="KeypairOrderBy",
)
class KeypairOrderByGQL(PydanticInputMixin[KeypairOrderBy]):
    """OrderBy for keypair queries."""

    field: KeypairOrderFieldGQL = KeypairOrderFieldGQL.CREATED_AT
    direction: OrderDirection = OrderDirection.DESC
