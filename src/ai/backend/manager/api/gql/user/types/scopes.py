"""User GraphQL scope types."""

from __future__ import annotations

from uuid import UUID

import strawberry

from ai.backend.common.dto.manager.v2.user.types import DomainUserScope, ProjectUserScope
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Scope for querying users within a specific domain. Used to restrict user queries to a particular domain context.",
        added_version="26.2.0",
    ),
    name="DomainUserV2Scope",
)
class DomainUserScopeGQL(PydanticInputMixin[DomainUserScope]):
    """Scope for domain-level user queries."""

    domain_name: str = strawberry.field(
        description="Domain name to scope the user query. Only users belonging to this domain will be returned."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Scope for querying users within a specific project. Used to restrict user queries to members of a particular project.",
        added_version="26.2.0",
    ),
    name="ProjectUserV2Scope",
)
class ProjectUserScopeGQL(PydanticInputMixin[ProjectUserScope]):
    """Scope for project-level user queries."""

    project_id: UUID = strawberry.field(
        description="Project UUID to scope the user query. Only users who are members of this project will be returned."
    )
