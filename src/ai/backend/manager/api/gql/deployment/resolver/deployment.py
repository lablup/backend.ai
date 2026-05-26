"""Deployment resolver functions."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from uuid import UUID

from strawberry import ID, Info
from strawberry.relay import PageInfo

from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.v2.deployment.request import (
    ReplaceDeploymentOptionsInput,
    SearchDeploymentsInput,
)
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import encode_cursor, resolve_global_id
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
    gql_root_field,
    gql_subscription,
)
from ai.backend.manager.api.gql.deployment.types.deployment import (
    AdminRefreshDeploymentRevisionsPayload,
    CreateDeploymentInput,
    CreateDeploymentPayload,
    DeleteDeploymentInput,
    DeleteDeploymentPayload,
    DeploymentFilter,
    DeploymentOrderBy,
    DeploymentStatusChangedPayload,
    ModelDeployment,
    ModelDeploymentConnection,
    ModelDeploymentEdge,
    ProjectDeploymentScopeGQL,
    ReplaceDeploymentOptionsInputGQL,
    ReplaceDeploymentOptionsPayload,
    RevisionRefreshResult,
    SyncReplicaInput,
    SyncReplicaPayload,
    UpdateDeploymentInput,
    UpdateDeploymentPayload,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only
from ai.backend.manager.errors.user import UserNotFound

# Query resolvers


@gql_root_field(
    BackendAIGQLMeta(
        added_version="25.16.0",
        description="List all deployments (superadmin only).",
    )
)  # type: ignore[misc]
async def admin_deployments(
    info: Info[StrawberryGQLContext],
    filter: DeploymentFilter | None = None,
    order_by: list[DeploymentOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ModelDeploymentConnection | None:
    """List all deployments (superadmin only)."""
    check_admin_only()
    pydantic_filter = filter.to_pydantic() if filter else None
    pydantic_order = [o.to_pydantic() for o in order_by] if order_by else None
    payload = await info.context.adapters.deployment.admin_search(
        SearchDeploymentsInput(
            filter=pydantic_filter,
            order=pydantic_order,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )
    nodes = [ModelDeployment.from_pydantic(item) for item in payload.items]
    edges = [ModelDeploymentEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]
    return ModelDeploymentConnection(
        count=payload.total_count,
        edges=edges,
        page_info=PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
    )


@gql_root_field(
    BackendAIGQLMeta(
        added_version="25.19.0",
        description="List deployments within a specific project.",
    )
)  # type: ignore[misc]
async def project_deployments(
    info: Info[StrawberryGQLContext],
    scope: ProjectDeploymentScopeGQL,
    filter: DeploymentFilter | None = None,
    order_by: list[DeploymentOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ModelDeploymentConnection | None:
    """List deployments within a specific project."""
    pydantic_filter = filter.to_pydantic() if filter else None
    pydantic_order = [o.to_pydantic() for o in order_by] if order_by else None
    payload = await info.context.adapters.deployment.project_search(
        scope.project_id,
        SearchDeploymentsInput(
            filter=pydantic_filter,
            order=pydantic_order,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
    )
    nodes = [ModelDeployment.from_pydantic(item) for item in payload.items]
    edges = [ModelDeploymentEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]
    return ModelDeploymentConnection(
        count=payload.total_count,
        edges=edges,
        page_info=PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
    )


@gql_root_field(
    BackendAIGQLMeta(
        added_version="25.19.0",
        description="List deployments owned by the current user.",
    )
)  # type: ignore[misc]
async def my_deployments(
    info: Info[StrawberryGQLContext],
    filter: DeploymentFilter | None = None,
    order_by: list[DeploymentOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ModelDeploymentConnection | None:
    """List deployments owned by the current user."""
    pydantic_filter = filter.to_pydantic() if filter else None
    pydantic_order = [o.to_pydantic() for o in order_by] if order_by else None
    payload = await info.context.adapters.deployment.my_search(
        SearchDeploymentsInput(
            filter=pydantic_filter,
            order=pydantic_order,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
    )
    nodes = [ModelDeployment.from_pydantic(item) for item in payload.items]
    edges = [ModelDeploymentEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]
    return ModelDeploymentConnection(
        count=payload.total_count,
        edges=edges,
        page_info=PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
    )


@gql_root_field(
    BackendAIGQLMeta(added_version="25.16.0", description="Get a specific deployment by ID.")
)  # type: ignore[misc]
async def deployment(id: ID, info: Info[StrawberryGQLContext]) -> ModelDeployment | None:
    """Get a specific deployment by ID."""
    _, deployment_id = resolve_global_id(id)
    node = await info.context.adapters.deployment.get(DeploymentID(UUID(deployment_id)))
    return ModelDeployment.from_pydantic(node)


# Mutation resolvers


@gql_mutation(BackendAIGQLMeta(added_version="25.16.0", description="Create model deployment."))
async def create_model_deployment(
    input: CreateDeploymentInput, info: Info[StrawberryGQLContext]
) -> CreateDeploymentPayload | None:
    """Create a new model deployment."""
    user_data = current_user()
    if user_data is None:
        raise UserNotFound("User not found in context")
    payload = await info.context.adapters.deployment.create(input.to_pydantic(), user_data.user_id)
    return CreateDeploymentPayload(deployment=ModelDeployment.from_pydantic(payload.deployment))


@gql_mutation(BackendAIGQLMeta(added_version="25.16.0", description="Update model deployment."))
async def update_model_deployment(
    input: UpdateDeploymentInput, info: Info[StrawberryGQLContext]
) -> UpdateDeploymentPayload | None:
    """Update an existing model deployment."""
    payload = await info.context.adapters.deployment.update(
        input.to_pydantic(), DeploymentID(UUID(input.id))
    )
    return UpdateDeploymentPayload(deployment=ModelDeployment.from_pydantic(payload.deployment))


@gql_mutation(BackendAIGQLMeta(added_version="25.16.0", description="Delete model deployment."))
async def delete_model_deployment(
    input: DeleteDeploymentInput, info: Info[StrawberryGQLContext]
) -> DeleteDeploymentPayload | None:
    """Delete a model deployment."""
    await info.context.adapters.deployment.delete(input.to_pydantic())
    return DeleteDeploymentPayload(id=input.id)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Fully replace the ``options`` surface of a deployment. "
            "Replace semantics — the supplied payload is the complete new value."
        ),
    )
)
async def replace_deployment_options(
    input: ReplaceDeploymentOptionsInputGQL, info: Info[StrawberryGQLContext]
) -> ReplaceDeploymentOptionsPayload | None:
    """Replace the options surface of a deployment.

    GQL input carries the target ``deployment_id`` and the full ``options``
    payload together; REST equivalent carries the id in the path. Only the
    refreshed options surface is returned (the server path uses
    ``UPDATE ... RETURNING`` and does not re-read the surrounding
    deployment node).
    """
    gql_pydantic = input.to_pydantic()
    rest_body = ReplaceDeploymentOptionsInput(options=gql_pydantic.options)
    payload = await info.context.adapters.deployment.replace_options(
        deployment_id=gql_pydantic.deployment_id,
        input=rest_body,
    )
    return ReplaceDeploymentOptionsPayload.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="25.16.0",
        description="Force syncs up-to-date replica information. In normal situations this will be automatically handled by Backend.AI schedulers.",
    )
)
async def sync_replicas(
    input: SyncReplicaInput, info: Info[StrawberryGQLContext]
) -> SyncReplicaPayload | None:
    payload = await info.context.adapters.deployment.sync_replicas(input.to_pydantic())
    return SyncReplicaPayload(success=payload.success)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.3",
        description=(
            "Rebuild and activate a fresh revision for every active deployment (superadmin). "
            "Used to repair deployments whose current revision has stale or missing "
            "model_definition after backing store migrations."
        ),
    )
)
async def admin_refresh_deployment_revisions(
    info: Info[StrawberryGQLContext],
) -> AdminRefreshDeploymentRevisionsPayload | None:
    check_admin_only()
    payload = await info.context.adapters.deployment.admin_refresh_deployment_revisions()
    return AdminRefreshDeploymentRevisionsPayload(
        results=[
            RevisionRefreshResult(
                deployment_id=r.deployment_id,
                new_revision_id=r.new_revision_id,
                success=r.success,
                failure_reason=r.failure_reason,
            )
            for r in payload.results
        ]
    )


# Subscription resolvers


@gql_subscription(
    BackendAIGQLMeta(added_version="25.16.0", description="Subscribe to deployment status changes.")
)
async def deployment_status_changed(
    info: Info[StrawberryGQLContext],
) -> AsyncGenerator[DeploymentStatusChangedPayload, None]:
    """Subscribe to deployment status changes."""
    # TODO: Implement actual subscription logic using pub/sub system
    raise NotImplementedError("Subscription not implemented")
    yield  # type: ignore[unreachable]  # Makes this an async generator
