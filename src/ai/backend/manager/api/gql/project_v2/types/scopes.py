"""Project V2 GraphQL scope types."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.group.types import DomainProjectScopeDTO
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Scope for querying projects within a specific domain. Used to restrict project queries to a particular domain context.",
        added_version="26.2.0",
    ),
    name="DomainProjectV2Scope",
)
class DomainProjectScope(PydanticInputMixin[DomainProjectScopeDTO]):
    """Scope for domain-level project queries."""

    domain_name: str = gql_field(
        description="Domain name to scope the query. Only projects belonging to this domain will be returned."
    )
