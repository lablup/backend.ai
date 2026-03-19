"""Project V2 GraphQL scope types."""

from __future__ import annotations

import strawberry

from ai.backend.common.dto.manager.v2.group.types import DomainProjectScopeDTO


@strawberry.experimental.pydantic.input(
    model=DomainProjectScopeDTO,
    name="DomainProjectV2Scope",
    description=(
        "Added in 26.2.0. Scope for querying projects within a specific domain. "
        "Used to restrict project queries to a particular domain context."
    ),
)
class DomainProjectScope:
    """Scope for domain-level project queries."""

    domain_name: str = strawberry.field(
        description="Domain name to scope the query. Only projects belonging to this domain will be returned."
    )

    def to_pydantic(self) -> DomainProjectScopeDTO:
        return DomainProjectScopeDTO(domain_name=self.domain_name)
