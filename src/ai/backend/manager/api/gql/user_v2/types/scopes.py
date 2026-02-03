"""User V2 GraphQL scope types."""

from __future__ import annotations

from uuid import UUID

import strawberry


@strawberry.input(
    name="DomainUserScope",
    description=(
        "Added in 26.2.0. Scope for querying users within a specific domain. "
        "Used to restrict user queries to a particular domain context."
    ),
)
class DomainUserScope:
    """Scope for domain-level user queries."""

    domain_name: str = strawberry.field(
        description="Domain name to scope the user query. Only users belonging to this domain will be returned."
    )


@strawberry.input(
    name="ProjectUserScope",
    description=(
        "Added in 26.2.0. Scope for querying users within a specific project. "
        "Used to restrict user queries to members of a particular project."
    ),
)
class ProjectUserScope:
    """Scope for project-level user queries."""

    project_id: UUID = strawberry.field(
        description="Project UUID to scope the user query. Only users who are members of this project will be returned."
    )
