"""Project V2 GraphQL scope types."""

from __future__ import annotations

import strawberry

from ai.backend.common.dto.manager.v2.group.types import DomainProjectScopeDTO
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_pydantic_input,
)


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Scope for querying projects within a specific domain. Used to restrict project queries to a particular domain context.",
        added_version="26.2.0",
    ),
    model=DomainProjectScopeDTO,
    name="DomainProjectV2Scope",
)
class DomainProjectScope:
    """Scope for domain-level project queries."""

    domain_name: str = strawberry.field(
        description="Domain name to scope the query. Only projects belonging to this domain will be returned."
    )

    def to_pydantic(self) -> DomainProjectScopeDTO:
        return DomainProjectScopeDTO(domain_name=self.domain_name)
