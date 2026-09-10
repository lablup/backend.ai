"""Deployment GraphQL scope types."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.deployment.types import DeploymentScope
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
            "Scope for the scoped deployment query. Each list is OR'd internally and "
            "across lists, and every scope named is authorized before the read runs."
        ),
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="DeploymentScope",
)
class DeploymentScopeGQL(PydanticInputMixin[DeploymentScope]):
    """The scopes a deployment read is answered for."""

    domain: list[UUIDScopeGQL] | None = gql_field(
        default=None, description="Domains whose deployments are being read."
    )
    project: list[UUIDScopeGQL] | None = gql_field(
        default=None, description="Projects whose deployments are being read."
    )
    user: list[UUIDScopeGQL] | None = gql_field(
        default=None, description="Users whose deployments are being read."
    )
