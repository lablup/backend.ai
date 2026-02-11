"""Project V2 GraphQL scope types."""

from __future__ import annotations

import strawberry


@strawberry.input(
    name="DomainProjectV2Scope",
    description=(
        "Added in 26.2.0. Scope for querying projects within a specific domain. "
        "Used to restrict project queries to a particular domain context."
    ),
)
class DomainProjectV2Scope:
    """Scope for domain-level project queries."""

    domain_name: str = strawberry.field(
        description="Domain name to scope the query. Only projects belonging to this domain will be returned."
    )
