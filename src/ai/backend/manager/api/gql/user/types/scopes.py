"""User GraphQL scope types."""

from __future__ import annotations

from uuid import UUID

import strawberry

from ai.backend.common.dto.manager.v2.user.types import DomainUserScope, ProjectUserScope
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_pydantic_input,
)


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Scope for querying users within a specific domain. Used to restrict user queries to a particular domain context.",
        added_version="26.2.0",
    ),
    model=DomainUserScope,
    name="DomainUserV2Scope",
)
class DomainUserScopeGQL:
    """Scope for domain-level user queries."""

    domain_name: str = strawberry.field(
        description="Domain name to scope the user query. Only users belonging to this domain will be returned."
    )

    def to_pydantic(self) -> DomainUserScope:
        return DomainUserScope(domain_name=self.domain_name)


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Scope for querying users within a specific project. Used to restrict user queries to members of a particular project.",
        added_version="26.2.0",
    ),
    model=ProjectUserScope,
    name="ProjectUserV2Scope",
)
class ProjectUserScopeGQL:
    """Scope for project-level user queries."""

    project_id: UUID = strawberry.field(
        description="Project UUID to scope the user query. Only users who are members of this project will be returned."
    )

    def to_pydantic(self) -> ProjectUserScope:
        return ProjectUserScope(project_id=self.project_id)
