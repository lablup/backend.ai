"""Deployment resolver functions."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import PurePosixPath
from uuid import UUID, uuid4

import strawberry
from strawberry import ID, Info
from strawberry.relay import PageInfo

from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.v2.deployment.request import AdminSearchDeploymentsInput
from ai.backend.common.dto.manager.v2.deployment.request import (
    CreateDeploymentInput as CreateDeploymentInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    RevisionInput as RevisionInputDTO,
)
from ai.backend.common.types import RuntimeVariant
from ai.backend.manager.api.gql.base import encode_cursor, resolve_global_id
from ai.backend.manager.api.gql.deployment.types.deployment import (
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
    SyncReplicaInput,
    SyncReplicaPayload,
    UpdateDeploymentInput,
    UpdateDeploymentPayload,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.data.deployment.creator import (
    DeploymentPolicyConfig,
    ModelRevisionCreator,
    NewDeploymentCreator,
    VFolderMountsCreator,
)
from ai.backend.manager.data.deployment.types import (
    DeploymentMetadata,
    DeploymentNetworkSpec,
    ExecutionSpec,
    MountInfo,
    ReplicaSpec,
    ResourceSpec,
)
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.deployment_policy.row import BlueGreenSpec, RollingUpdateSpec
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.repositories.base import Updater
from ai.backend.manager.repositories.deployment.updaters import (
    DeploymentMetadataUpdaterSpec,
    DeploymentNetworkSpecUpdaterSpec,
    DeploymentPolicyUpdaterSpec,
    DeploymentUpdaterSpec,
    ReplicaSpecUpdaterSpec,
    RevisionStateUpdaterSpec,
)
from ai.backend.manager.services.deployment.actions.create_deployment import (
    CreateDeploymentAction,
)
from ai.backend.manager.services.deployment.actions.destroy_deployment import (
    DestroyDeploymentAction,
)
from ai.backend.manager.services.deployment.actions.get_deployment_by_id import (
    GetDeploymentByIdAction,
)
from ai.backend.manager.services.deployment.actions.sync_replicas import SyncReplicaAction
from ai.backend.manager.services.deployment.actions.update_deployment import UpdateDeploymentAction
from ai.backend.manager.types import OptionalState, TriState


def _build_model_revision_creator(revision_dto: RevisionInputDTO) -> ModelRevisionCreator:
    resource_spec = ResourceSpec(
        cluster_mode=revision_dto.cluster_mode,
        cluster_size=revision_dto.cluster_size,
        resource_slots=revision_dto.resource_slots,
        resource_opts=revision_dto.resource_opts,
    )
    extra_mounts = [
        MountInfo(
            vfolder_id=m.vfolder_id,
            kernel_path=PurePosixPath(m.mount_destination) if m.mount_destination else None,
        )
        for m in (revision_dto.extra_mounts or [])
    ]
    mounts = VFolderMountsCreator(
        model_vfolder_id=revision_dto.model_vfolder_id,
        model_definition_path=revision_dto.model_definition_path,
        model_mount_destination=revision_dto.model_mount_destination,
        extra_mounts=extra_mounts,
    )
    execution = ExecutionSpec(
        environ=dict(revision_dto.environ) if revision_dto.environ else None,
        runtime_variant=RuntimeVariant(revision_dto.runtime_variant),
    )
    return ModelRevisionCreator(
        image_id=revision_dto.image_id,
        resource_spec=resource_spec,
        mounts=mounts,
        execution=execution,
    )


def _build_deployment_policy_config(dto: CreateDeploymentInputDTO) -> DeploymentPolicyConfig:
    from ai.backend.common.data.model_deployment.types import DeploymentStrategy

    spec: RollingUpdateSpec | BlueGreenSpec = RollingUpdateSpec()
    match dto.strategy:
        case DeploymentStrategy.ROLLING:
            spec = (
                RollingUpdateSpec(
                    max_surge=dto.rolling_update.max_surge,
                    max_unavailable=dto.rolling_update.max_unavailable,
                )
                if dto.rolling_update
                else RollingUpdateSpec()
            )
        case DeploymentStrategy.BLUE_GREEN:
            spec = (
                BlueGreenSpec(
                    auto_promote=dto.blue_green.auto_promote,
                    promote_delay_seconds=dto.blue_green.promote_delay_seconds,
                )
                if dto.blue_green
                else BlueGreenSpec()
            )
    return DeploymentPolicyConfig(
        strategy=dto.strategy,
        strategy_spec=spec,
        rollback_on_failure=dto.rollback_on_failure,
    )


def _build_deployment_creator(dto: CreateDeploymentInputDTO) -> NewDeploymentCreator:
    user_data = current_user()
    if user_data is None:
        raise UserNotFound("User not found in context")
    name = dto.name or f"deployment-{uuid4().hex[:8]}"
    tag = ",".join(dto.tags) if dto.tags else None
    metadata = DeploymentMetadata(
        name=name,
        domain=dto.domain_name,
        project=dto.project_id,
        resource_group=dto.initial_revision.resource_group,
        created_user=user_data.user_id,
        session_owner=user_data.user_id,
        created_at=None,
        revision_history_limit=10,
        tag=tag,
    )
    return NewDeploymentCreator(
        metadata=metadata,
        replica_spec=ReplicaSpec(replica_count=dto.desired_replica_count),
        network=DeploymentNetworkSpec(
            open_to_public=dto.open_to_public,
            preferred_domain_name=dto.preferred_domain_name,
        ),
        model_revision=_build_model_revision_creator(dto.initial_revision),
        policy=_build_deployment_policy_config(dto),
    )


def _build_deployment_updater(
    deployment_id: UUID, input: UpdateDeploymentInput
) -> Updater[EndpointRow]:
    metadata_spec: DeploymentMetadataUpdaterSpec | None = None
    if input.name is not None or input.tags is not None:
        tag_str: str | None = None
        if input.tags is not None:
            tag_str = ",".join(input.tags)
        metadata_spec = DeploymentMetadataUpdaterSpec(
            name=OptionalState[str].from_graphql(input.name),
            tag=TriState[str].from_graphql(tag_str),
        )
    replica_spec: ReplicaSpecUpdaterSpec | None = None
    if input.desired_replica_count is not None:
        replica_spec = ReplicaSpecUpdaterSpec(
            desired_replica_count=OptionalState[int].from_graphql(input.desired_replica_count),
        )
    network_spec: DeploymentNetworkSpecUpdaterSpec | None = None
    if input.open_to_public is not None:
        network_spec = DeploymentNetworkSpecUpdaterSpec(
            open_to_public=OptionalState[bool].from_graphql(input.open_to_public),
        )
    revision_state_spec: RevisionStateUpdaterSpec | None = None
    if input.active_revision_id is not None:
        revision_state_spec = RevisionStateUpdaterSpec(
            current_revision=TriState[UUID].from_graphql(UUID(input.active_revision_id)),
        )
    spec = DeploymentUpdaterSpec(
        metadata=metadata_spec,
        replica_spec=replica_spec,
        network=network_spec,
        revision_state=revision_state_spec,
    )
    return Updater(spec=spec, pk_value=deployment_id)


def _build_deployment_policy_updater_spec(
    input: UpdateDeploymentInput,
) -> DeploymentPolicyUpdaterSpec | None:
    if input.default_deployment_strategy is None:
        return None
    creator = input.default_deployment_strategy.to_policy_config()
    return DeploymentPolicyUpdaterSpec(
        strategy=OptionalState.update(creator.strategy),
        strategy_spec=OptionalState.update(creator.strategy_spec),
        rollback_on_failure=OptionalState.update(creator.rollback_on_failure),
    )


# Query resolvers


@strawberry.field(description="Added in 25.16.0")  # type: ignore[misc]
async def deployments(
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
    """List deployments with optional filtering and pagination (admin, all deployments)."""
    pydantic_filter = filter.to_pydantic() if filter else None
    pydantic_order = [o.to_pydantic() for o in order_by] if order_by else None
    payload = await info.context.adapters.deployment.admin_search(
        AdminSearchDeploymentsInput(
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


@strawberry.field(description="Added in 25.16.0")  # type: ignore[misc]
async def deployment(id: ID, info: Info[StrawberryGQLContext]) -> ModelDeployment | None:
    """Get a specific deployment by ID."""
    _, deployment_id = resolve_global_id(id)
    processor = info.context.processors.deployment
    result = await processor.get_deployment_by_id.wait_for_complete(
        GetDeploymentByIdAction(deployment_id=UUID(deployment_id))
    )
    return ModelDeployment.from_dataclass(result.data)


# Mutation resolvers


@strawberry.mutation(description="Added in 25.16.0")  # type: ignore[misc]
async def create_model_deployment(
    input: CreateDeploymentInput, info: Info[StrawberryGQLContext]
) -> CreateDeploymentPayload:
    """Create a new model deployment."""
    processor = info.context.processors.deployment
    result = await processor.create_deployment.wait_for_complete(
        CreateDeploymentAction(creator=_build_deployment_creator(input.to_pydantic()))
    )
    return CreateDeploymentPayload(deployment=ModelDeployment.from_dataclass(result.data))


@strawberry.mutation(description="Added in 25.16.0")  # type: ignore[misc]
async def update_model_deployment(
    input: UpdateDeploymentInput, info: Info[StrawberryGQLContext]
) -> UpdateDeploymentPayload:
    """Update an existing model deployment."""
    _, deployment_id = resolve_global_id(input.id)
    deployment_uuid = UUID(deployment_id)
    processor = info.context.processors.deployment
    action_result = await processor.update_deployment.wait_for_complete(
        UpdateDeploymentAction(updater=_build_deployment_updater(deployment_uuid, input))
    )
    return UpdateDeploymentPayload(deployment=ModelDeployment.from_dataclass(action_result.data))


@strawberry.mutation(description="Added in 25.16.0")  # type: ignore[misc]
async def delete_model_deployment(
    input: DeleteDeploymentInput, info: Info[StrawberryGQLContext]
) -> DeleteDeploymentPayload:
    """Delete a model deployment."""
    _, deployment_id = resolve_global_id(input.id)
    deployment_processor = info.context.processors.deployment
    _ = await deployment_processor.destroy_deployment.wait_for_complete(
        DestroyDeploymentAction(endpoint_id=UUID(deployment_id))
    )
    return DeleteDeploymentPayload(id=input.id)


@strawberry.mutation(  # type: ignore[misc]
    description="Added in 25.16.0. Force syncs up-to-date replica information. In normal situations this will be automatically handled by Backend.AI schedulers"
)
async def sync_replicas(
    input: SyncReplicaInput, info: Info[StrawberryGQLContext]
) -> SyncReplicaPayload:
    _, deployment_id = resolve_global_id(input.model_deployment_id)
    deployment_processor = info.context.processors.deployment
    await deployment_processor.sync_replicas.wait_for_complete(
        SyncReplicaAction(deployment_id=UUID(deployment_id))
    )
    return SyncReplicaPayload(success=True)


# Subscription resolvers


@strawberry.subscription(description="Added in 25.16.0. Subscribe to deployment status changes")  # type: ignore[misc]
async def deployment_status_changed(
    info: Info[StrawberryGQLContext],
) -> AsyncGenerator[DeploymentStatusChangedPayload, None]:
    """Subscribe to deployment status changes."""
    # TODO: Implement actual subscription logic using pub/sub system
    raise NotImplementedError("Subscription not implemented")
    yield  # type: ignore[unreachable]  # Makes this an async generator
