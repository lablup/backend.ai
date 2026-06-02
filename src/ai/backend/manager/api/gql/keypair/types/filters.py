"""Keypair GraphQL filter and order-by types."""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from ai.backend.common.dto.manager.v2.keypair.request import (
    KeypairFilter as KeypairFilterDTO,
)
from ai.backend.common.dto.manager.v2.keypair.request import (
    KeypairOrderBy as KeypairOrderByDTO,
)
from ai.backend.common.dto.manager.v2.keypair.request import (
    KeypairUserNestedFilter as KeypairUserNestedFilterDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import (
    DateTimeFilter,
    OrderDirection,
    StringFilter,
    UUIDFilter,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_added_field,
    gql_enum,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Nested filter for the user that owns a keypair. "
            "Filters keypairs to those owned by a user matching the specified conditions."
        ),
    ),
    name="KeypairUserNestedFilter",
)
class KeypairUserNestedFilterGQL(PydanticInputMixin[KeypairUserNestedFilterDTO]):
    """Nested filter for the keypair owner."""

    user_id: UUIDFilter | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description=(
            "Filter input for keypair queries. "
            "Supports filtering by active state, admin flag, and access key. "
            "Multiple filters can be combined using AND, OR, and NOT logical operators."
        ),
        added_version="26.4.2",
    ),
    name="KeypairFilter",
)
class KeypairFilterGQL(PydanticInputMixin[KeypairFilterDTO]):
    """Filter for keypair queries."""

    is_active: bool | None = None
    is_admin: bool | None = None
    access_key: StringFilter | None = None
    resource_policy: StringFilter | None = None
    user: KeypairUserNestedFilterGQL | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description=(
                "Filter keypairs by their owner. "
                "A keypair matches if its owner satisfies the conditions."
            ),
        ),
        default=None,
    )
    created_at: DateTimeFilter | None = None
    last_used: DateTimeFilter | None = None
    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.4.2",
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
        added_version="26.4.2",
    ),
    name="KeypairOrderBy",
)
class KeypairOrderByGQL(PydanticInputMixin[KeypairOrderByDTO]):
    """OrderBy for keypair queries."""

    field: KeypairOrderFieldGQL = KeypairOrderFieldGQL.CREATED_AT
    direction: OrderDirection = OrderDirection.DESC
