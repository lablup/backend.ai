"""Project V2 GraphQL scope types."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.group.types import DomainProjectScopeDTO, ProjectScope
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin
from ai.backend.manager.api.gql.rbac.types.scope import UUIDScopeGQL


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


@gql_pydantic_input(
    BackendAIGQLMeta(
        description=(
            "Scope for the scoped project query. Each list is OR'd internally and across "
            "lists, and every scope named is authorized before the read runs."
        ),
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="ProjectScope",
)
class ProjectScopeGQL(PydanticInputMixin[ProjectScope]):
    """The scopes a project read is answered for."""

    domain: list[UUIDScopeGQL] | None = gql_field(
        default=None, description="Domains whose projects are being read."
    )
    user: list[UUIDScopeGQL] | None = gql_field(
        default=None, description="Users whose project memberships are being read."
    )
