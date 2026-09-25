"""Deployment GraphQL scope types."""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.dto.manager.v2.deployment.types import (
    DeploymentScope,
    DeploymentUsage,
    DeploymentUses,
)
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
        description="Entities a deployment uses, whose ids narrow the read.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="DeploymentUses",
)
class DeploymentUsesGQL(PydanticInputMixin[DeploymentUses]):
    """The entities a deployment uses, whose ids narrow the read."""

    resource_group: list[UUID] | None = gql_field(
        default=None, description="Resource groups the deployment runs in."
    )
    image: list[UUID] | None = gql_field(
        default=None,
        description=("Images the deployment's live replica group names in its current revision."),
    )
    vfolder: list[UUID] | None = gql_field(
        default=None,
        description=(
            "VFolders the deployment's live replica group names as the model of its current "
            "revision."
        ),
    )
    session: list[UUID] | None = gql_field(
        default=None, description="Sessions the deployment's route rows serve as their replicas."
    )
    runtime_variant: list[UUID] | None = gql_field(
        default=None, description="Runtime variants the deployment's revisions name."
    )
    deployment_preset: list[UUID] | None = gql_field(
        default=None, description="Presets the deployment's revisions name."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description=(
            "Uses narrowing a deployment query; every id is AND-ed. The caller must be able "
            "to read each listed entity, or the request is refused. Only deployments the caller "
            "can read are returned, even when a listed entity is tied to others."
        ),
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="DeploymentUsage",
)
class DeploymentUsageGQL(PydanticInputMixin[DeploymentUsage]):
    """The uses that narrow a deployment read."""

    uses: DeploymentUsesGQL | None = gql_field(
        default=None, description="Entities the deployment uses, whose ids narrow the read."
    )
