"""Domain V2 GraphQL scope types."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.domain.types import DomainScope
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import UUIDScopeGQL
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin


@gql_pydantic_input(
    BackendAIGQLMeta(
        description=(
            "Scope for the scoped domain query. Each list is OR'd internally, and every "
            "scope named is authorized before the read runs."
        ),
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="DomainScope",
)
class DomainScopeGQL(PydanticInputMixin[DomainScope]):
    """The scopes a domain read is answered for."""

    resource_group: list[UUIDScopeGQL] | None = gql_field(
        default=None, description="Resource groups whose domains are being read."
    )
