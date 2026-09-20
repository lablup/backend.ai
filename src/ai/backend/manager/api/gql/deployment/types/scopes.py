"""Deployment GraphQL scope types."""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.dto.manager.v2.deployment.types import DeploymentScope, DeploymentUsedBy
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
    name="DeploymentSearchScope",
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


@gql_pydantic_input(
    BackendAIGQLMeta(
        description=(
            "Entities whose use narrows a deployment query; every id is AND-ed. The caller "
            "must be able to read each listed entity, or the request is refused. Only "
            "deployments the caller can read are returned, even when a listed entity uses "
            "others."
        ),
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="DeploymentUsedBy",
)
class DeploymentUsedByGQL(PydanticInputMixin[DeploymentUsedBy]):
    """The entities whose use of a deployment narrows the read."""

    resource_group: list[UUID] | None = gql_field(
        default=None, description="Resource groups the deployment runs in."
    )
