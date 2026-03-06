"""
Adapters to convert deployment DTOs to repository BatchQuerier objects.
Handles conversion of filter, order, and pagination parameters.
Also provides data-to-DTO conversion functions.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import PurePosixPath
from typing import Any
from uuid import UUID, uuid4

from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.data.model_deployment.types import (
    RouteStatus as CommonRouteStatus,
)
from ai.backend.common.data.model_deployment.types import (
    RouteTrafficStatus as CommonRouteTrafficStatus,
)
from ai.backend.common.dto.manager.deployment import (
    ClusterConfigDTO,
    CreateDeploymentPolicyRequest,
    CreateDeploymentRequest,
    DeploymentDTO,
    DeploymentFilter,
    DeploymentOrder,
    DeploymentPolicyDTO,
    ModelMountConfigDTO,
    ModelRuntimeConfigDTO,
    NetworkConfigDTO,
    ReplicaStateDTO,
    ResourceConfigDTO,
    RevisionDTO,
    RevisionFilter,
    RevisionInput,
    RevisionOrder,
    RouteDTO,
    RouteFilter,
    RouteOrder,
    SearchDeploymentsRequest,
    SearchRevisionsRequest,
    SearchRoutesRequest,
    UpdateDeploymentPolicyRequest,
)
from ai.backend.common.dto.manager.deployment.types import (
    DeploymentOrderField,
    OrderDirection,
    RevisionOrderField,
    RouteOrderField,
)
from ai.backend.common.types import ClusterMode, RuntimeVariant
from ai.backend.manager.api.rest.adapter import BaseFilterAdapter
from ai.backend.manager.data.deployment.creator import (
    DeploymentPolicyConfig,
    DeploymentPolicyCreator,
    ModelRevisionCreator,
    NewDeploymentCreator,
    VFolderMountsCreator,
)
from ai.backend.manager.data.deployment.modifier import DeploymentPolicyModifier
from ai.backend.manager.data.deployment.types import (
    DeploymentMetadata,
    DeploymentNetworkSpec,
    DeploymentPolicyData,
    ExecutionSpec,
    ModelDeploymentData,
    ModelRevisionData,
    MountInfo,
    ReplicaSpec,
    ResourceSpec,
    RouteInfo,
)
from ai.backend.manager.data.deployment.types import (
    RouteStatus as ManagerRouteStatus,
)
from ai.backend.manager.data.deployment.types import (
    RouteTrafficStatus as ManagerRouteTrafficStatus,
)
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.deployment import IncompleteRevisionData
from ai.backend.manager.models.deployment_policy import BlueGreenSpec, RollingUpdateSpec
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.repositories.deployment.options import (
    DeploymentConditions,
    DeploymentOrders,
    RevisionConditions,
    RevisionOrders,
    RouteConditions,
    RouteOrders,
)
from ai.backend.manager.types import OptionalState

__all__ = (
    "AddRevisionAdapter",
    "CreateDeploymentAdapter",
    "CreateRevisionAdapter",
    "DeploymentAdapter",
    "DeploymentPolicyAdapter",
    "RevisionAdapter",
    "RouteAdapter",
    "build_revision_creator",
)


class DeploymentAdapter(BaseFilterAdapter):
    """Adapter for converting deployment requests to repository queries."""

    def convert_to_dto(self, data: ModelDeploymentData) -> DeploymentDTO:
        """Convert ModelDeploymentData to DTO."""
        current_revision = None
        if data.revision:
            revision_adapter = RevisionAdapter()
            current_revision = revision_adapter.convert_to_dto(data.revision)

        return DeploymentDTO(
            id=data.id,
            name=data.metadata.name,
            status=data.metadata.status,
            tags=data.metadata.tags,
            project_id=data.metadata.project_id,
            domain_name=data.metadata.domain_name,
            created_at=data.metadata.created_at,
            updated_at=data.metadata.updated_at,
            created_user_id=data.created_user_id,
            network_config=NetworkConfigDTO(
                open_to_public=data.network_access.open_to_public,
                url=data.network_access.url,
                preferred_domain_name=data.network_access.preferred_domain_name,
            ),
            replica_state=ReplicaStateDTO(
                desired_replica_count=data.replica_state.desired_replica_count,
                replica_ids=data.replica_state.replica_ids,
            ),
            default_deployment_strategy=data.default_deployment_strategy,
            current_revision=current_revision,
        )

    def build_querier(self, request: SearchDeploymentsRequest) -> BatchQuerier:
        """
        Build a BatchQuerier for deployments from search request.

        Args:
            request: Search request containing filter, order, and pagination

        Returns:
            BatchQuerier object with converted conditions, orders, and pagination
        """
        conditions = self._convert_filter(request.filter) if request.filter else []
        orders = [self._convert_order(request.order)] if request.order else []
        pagination = self._build_pagination(request.limit, request.offset)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(self, filter: DeploymentFilter) -> list[QueryCondition]:
        """Convert deployment filter to list of query conditions."""
        conditions: list[QueryCondition] = []

        # Name filter
        if filter.name is not None:
            condition = self.convert_string_filter(
                filter.name,
                contains_factory=DeploymentConditions.by_name_contains,
                equals_factory=DeploymentConditions.by_name_equals,
                starts_with_factory=DeploymentConditions.by_name_starts_with,
                ends_with_factory=DeploymentConditions.by_name_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        # Domain name filter
        if filter.domain_name is not None:
            condition = self.convert_string_filter(
                filter.domain_name,
                contains_factory=DeploymentConditions.by_domain_name_contains,
                equals_factory=DeploymentConditions.by_domain_name_equals,
                starts_with_factory=DeploymentConditions.by_domain_name_starts_with,
                ends_with_factory=DeploymentConditions.by_domain_name_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        # Project ID filter
        if filter.project_id is not None:
            conditions.append(DeploymentConditions.by_project_id(filter.project_id))

        return conditions

    def _convert_order(self, order: DeploymentOrder) -> QueryOrder:
        """Convert deployment order specification to query order."""
        ascending = order.direction == OrderDirection.ASC

        if order.field == DeploymentOrderField.NAME:
            return DeploymentOrders.name(ascending=ascending)
        if order.field == DeploymentOrderField.CREATED_AT:
            return DeploymentOrders.created_at(ascending=ascending)
        raise ValueError(f"Unknown order field: {order.field}")

    def _build_pagination(self, limit: int, offset: int) -> OffsetPagination:
        """Build pagination from limit and offset."""
        return OffsetPagination(limit=limit, offset=offset)


class RevisionAdapter(BaseFilterAdapter):
    """Adapter for converting revision requests to repository queries."""

    def convert_to_dto(self, data: ModelRevisionData) -> RevisionDTO:
        """Convert ModelRevisionData to DTO."""
        mount_config = data.model_mount_config
        if mount_config.vfolder_id is None:
            raise IncompleteRevisionData(f"Revision {data.id} has incomplete model mount config")
        return RevisionDTO(
            id=data.id,
            name=data.name,
            cluster_config=ClusterConfigDTO(
                mode=data.cluster_config.mode,
                size=data.cluster_config.size,
            ),
            resource_config=ResourceConfigDTO(
                resource_group_name=data.resource_config.resource_group_name,
                resource_slot=dict(data.resource_config.resource_slot),
            ),
            model_runtime_config=ModelRuntimeConfigDTO(
                runtime_variant=data.model_runtime_config.runtime_variant,
            ),
            model_mount_config=ModelMountConfigDTO(
                vfolder_id=mount_config.vfolder_id,
                mount_destination=mount_config.mount_destination or "",
                definition_path=mount_config.definition_path,
            ),
            created_at=data.created_at,
            image_id=data.image_id,
        )

    def build_querier(self, request: SearchRevisionsRequest) -> BatchQuerier:
        """
        Build a BatchQuerier for revisions from search request.

        Args:
            request: Search request containing filter, order, and pagination

        Returns:
            BatchQuerier object with converted conditions, orders, and pagination
        """
        conditions = self._convert_filter(request.filter) if request.filter else []
        orders = [self._convert_order(request.order)] if request.order else []
        pagination = self._build_pagination(request.limit, request.offset)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(self, filter: RevisionFilter) -> list[QueryCondition]:
        """Convert revision filter to list of query conditions."""
        conditions: list[QueryCondition] = []

        # Name filter
        if filter.name is not None:
            condition = self.convert_string_filter(
                filter.name,
                contains_factory=RevisionConditions.by_name_contains,
                equals_factory=RevisionConditions.by_name_equals,
                starts_with_factory=RevisionConditions.by_name_starts_with,
                ends_with_factory=RevisionConditions.by_name_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        # Deployment ID filter
        if filter.deployment_id is not None:
            conditions.append(RevisionConditions.by_deployment_id(filter.deployment_id))

        return conditions

    def _convert_order(self, order: RevisionOrder) -> QueryOrder:
        """Convert revision order specification to query order."""
        ascending = order.direction == OrderDirection.ASC

        if order.field == RevisionOrderField.NAME:
            return RevisionOrders.name(ascending=ascending)
        if order.field == RevisionOrderField.CREATED_AT:
            return RevisionOrders.created_at(ascending=ascending)
        raise ValueError(f"Unknown order field: {order.field}")

    def _build_pagination(self, limit: int, offset: int) -> OffsetPagination:
        """Build pagination from limit and offset."""
        return OffsetPagination(limit=limit, offset=offset)


class RouteAdapter(BaseFilterAdapter):
    """Adapter for converting route requests to repository queries."""

    def convert_to_dto(self, data: RouteInfo) -> RouteDTO:
        """Convert RouteInfo to DTO."""
        return RouteDTO(
            id=data.route_id,
            endpoint_id=data.endpoint_id,
            session_id=str(data.session_id) if data.session_id else None,
            status=CommonRouteStatus(data.status.value),
            traffic_ratio=data.traffic_ratio,
            created_at=data.created_at or datetime.now(tz=UTC),
            revision_id=data.revision_id,
            traffic_status=CommonRouteTrafficStatus(data.traffic_status.value),
            error_data=data.error_data,
        )

    def build_querier(self, request: SearchRoutesRequest) -> BatchQuerier:
        """
        Build a BatchQuerier for routes from search request.

        Args:
            request: Search request containing filter, order, and pagination

        Returns:
            BatchQuerier object with converted conditions, orders, and pagination
        """
        conditions = self._convert_filter(request.filter) if request.filter else []
        orders = [self._convert_order(request.order)] if request.order else []

        # Add cursor conditions if provided
        if request.cursor:
            if request.cursor_direction == "forward":
                conditions.append(RouteConditions.by_cursor_forward(request.cursor))
            elif request.cursor_direction == "backward":
                conditions.append(RouteConditions.by_cursor_backward(request.cursor))

        pagination = self._build_pagination(request.limit, request.offset)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(self, filter: RouteFilter) -> list[QueryCondition]:
        """Convert route filter to list of query conditions."""
        conditions: list[QueryCondition] = []

        # Deployment ID filter
        if filter.deployment_id is not None:
            conditions.append(RouteConditions.by_endpoint_id(filter.deployment_id))

        # Status filter - convert common types to manager types
        if filter.statuses is not None:
            manager_statuses = [ManagerRouteStatus(s.value) for s in filter.statuses]
            conditions.append(RouteConditions.by_statuses(manager_statuses))

        # Traffic status filter - convert common types to manager types
        if filter.traffic_statuses is not None:
            manager_traffic_statuses = [
                ManagerRouteTrafficStatus(s.value) for s in filter.traffic_statuses
            ]
            conditions.append(RouteConditions.by_traffic_statuses(manager_traffic_statuses))

        return conditions

    def _convert_order(self, order: RouteOrder) -> QueryOrder:
        """Convert route order specification to query order."""
        ascending = order.direction == OrderDirection.ASC

        if order.field == RouteOrderField.CREATED_AT:
            return RouteOrders.created_at(ascending=ascending)
        if order.field == RouteOrderField.STATUS:
            return RouteOrders.status(ascending=ascending)
        if order.field == RouteOrderField.TRAFFIC_RATIO:
            return RouteOrders.traffic_ratio(ascending=ascending)
        raise ValueError(f"Unknown order field: {order.field}")

    def _build_pagination(self, limit: int, offset: int) -> OffsetPagination:
        """Build pagination from limit and offset."""
        return OffsetPagination(limit=limit, offset=offset)


def build_revision_creator(revision_input: RevisionInput) -> ModelRevisionCreator:
    """Build ModelRevisionCreator from RevisionInput.

    Shared by AddRevisionAdapter and CreateDeploymentAdapter to avoid
    duplicated conversion logic.
    """
    resource_spec = ResourceSpec(
        cluster_mode=ClusterMode(revision_input.cluster_config.mode),
        cluster_size=revision_input.cluster_config.size,
        resource_slots=dict(revision_input.resource_config.resource_slots),
        resource_opts=(
            dict(revision_input.resource_config.resource_opts)
            if revision_input.resource_config.resource_opts
            else None
        ),
    )

    extra_mounts: list[MountInfo] = []
    if revision_input.extra_mounts:
        extra_mounts = [
            MountInfo(
                vfolder_id=mount.vfolder_id,
                kernel_path=PurePosixPath(mount.mount_destination)
                if mount.mount_destination
                else None,
            )
            for mount in revision_input.extra_mounts
        ]

    mounts = VFolderMountsCreator(
        model_vfolder_id=revision_input.model_mount_config.vfolder_id,
        model_definition_path=revision_input.model_mount_config.definition_path,
        model_mount_destination=revision_input.model_mount_config.mount_destination,
        extra_mounts=extra_mounts,
    )

    execution = ExecutionSpec(
        runtime_variant=RuntimeVariant(revision_input.model_runtime_config.runtime_variant),
        inference_runtime_config=(
            dict(revision_input.model_runtime_config.inference_runtime_config)
            if revision_input.model_runtime_config.inference_runtime_config
            else None
        ),
        environ=(
            dict(revision_input.model_runtime_config.environ)
            if revision_input.model_runtime_config.environ
            else None
        ),
    )

    return ModelRevisionCreator(
        image_id=revision_input.image.id,
        resource_spec=resource_spec,
        mounts=mounts,
        execution=execution,
    )


class AddRevisionAdapter:
    """Adapter for converting add revision request to ModelRevisionCreator."""

    @staticmethod
    def build_revision_creator(revision_input: RevisionInput) -> ModelRevisionCreator:
        """Build ModelRevisionCreator from revision input."""
        return build_revision_creator(revision_input)


class CreateDeploymentAdapter:
    """Adapter for converting create deployment request to creators."""

    def build_creator(
        self,
        request: CreateDeploymentRequest,
        user_uuid: UUID,
    ) -> NewDeploymentCreator:
        """
        Convert CreateDeploymentRequest to NewDeploymentCreator.

        Args:
            request: Create deployment request DTO
            user_uuid: UUID of the user creating the deployment

        Returns:
            NewDeploymentCreator for service layer
        """
        # Generate name if not provided
        name = request.metadata.name or f"deployment-{uuid4().hex[:8]}"
        tag = ",".join(request.metadata.tags) if request.metadata.tags else None

        # Build metadata
        metadata = DeploymentMetadata(
            name=name,
            domain=request.metadata.domain_name,
            project=request.metadata.project_id,
            resource_group=request.initial_revision.resource_config.resource_group,
            created_user=user_uuid,
            session_owner=user_uuid,
            created_at=None,
            revision_history_limit=10,
            tag=tag,
        )

        # Build replica spec
        replica_spec = ReplicaSpec(replica_count=request.desired_replica_count)

        # Build network spec
        network = DeploymentNetworkSpec(
            open_to_public=request.network_access.open_to_public,
            preferred_domain_name=request.network_access.preferred_domain_name,
        )

        # Build model revision creator
        model_revision = build_revision_creator(request.initial_revision)

        # Build policy config
        policy = self._build_policy_config(request.default_deployment_strategy)

        return NewDeploymentCreator(
            metadata=metadata,
            replica_spec=replica_spec,
            network=network,
            model_revision=model_revision,
            policy=policy,
        )

    def _build_policy_config(
        self,
        strategy_input: Any,  # DeploymentStrategyInput
    ) -> DeploymentPolicyConfig:
        """Build DeploymentPolicyConfig from strategy input."""
        strategy = DeploymentStrategy(strategy_input.type)

        strategy_spec: RollingUpdateSpec | BlueGreenSpec
        match strategy:
            case DeploymentStrategy.ROLLING:
                if strategy_input.rolling_update is None:
                    strategy_spec = RollingUpdateSpec(max_surge=1, max_unavailable=0)
                else:
                    strategy_spec = RollingUpdateSpec(
                        max_surge=strategy_input.rolling_update.max_surge,
                        max_unavailable=strategy_input.rolling_update.max_unavailable,
                    )
            case DeploymentStrategy.BLUE_GREEN:
                if strategy_input.blue_green is None:
                    strategy_spec = BlueGreenSpec(auto_promote=False, promote_delay_seconds=0)
                else:
                    strategy_spec = BlueGreenSpec(
                        auto_promote=strategy_input.blue_green.auto_promote,
                        promote_delay_seconds=strategy_input.blue_green.promote_delay_seconds,
                    )

        return DeploymentPolicyConfig(
            strategy=strategy,
            strategy_spec=strategy_spec,
            rollback_on_failure=strategy_input.rollback_on_failure,
        )


class CreateRevisionAdapter:
    """Adapter for converting create revision request to creators."""

    def build_creator(self, request: RevisionInput) -> ModelRevisionCreator:
        """
        Convert RevisionInput to ModelRevisionCreator.

        Args:
            request: Revision input DTO

        Returns:
            ModelRevisionCreator for service layer
        """
        return build_revision_creator(request)


class DeploymentPolicyAdapter:
    """Adapter for converting deployment policy data to DTOs and building specs."""

    def convert_to_dto(self, data: DeploymentPolicyData) -> DeploymentPolicyDTO:
        """Convert DeploymentPolicyData to DTO."""
        return DeploymentPolicyDTO(
            id=data.id,
            strategy=data.strategy,
            strategy_spec=data.strategy_spec.model_dump(),
            rollback_on_failure=data.rollback_on_failure,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )

    def build_creator(
        self, request: CreateDeploymentPolicyRequest, deployment_id: UUID
    ) -> DeploymentPolicyCreator:
        """Build DeploymentPolicyCreator from create request."""
        strategy = request.strategy

        strategy_spec: RollingUpdateSpec | BlueGreenSpec
        match strategy:
            case DeploymentStrategy.ROLLING:
                if request.rolling_update is not None:
                    strategy_spec = RollingUpdateSpec(
                        max_surge=request.rolling_update.max_surge,
                        max_unavailable=request.rolling_update.max_unavailable,
                    )
                else:
                    strategy_spec = RollingUpdateSpec(max_surge=1, max_unavailable=0)
            case DeploymentStrategy.BLUE_GREEN:
                if request.blue_green is not None:
                    strategy_spec = BlueGreenSpec(
                        auto_promote=request.blue_green.auto_promote,
                        promote_delay_seconds=request.blue_green.promote_delay_seconds,
                    )
                else:
                    strategy_spec = BlueGreenSpec(auto_promote=False, promote_delay_seconds=0)
            case _:
                raise InvalidAPIParameters(f"Unsupported deployment strategy: {strategy}")

        return DeploymentPolicyCreator(
            deployment_id=deployment_id,
            strategy=strategy,
            strategy_spec=strategy_spec,
            rollback_on_failure=request.rollback_on_failure,
        )

    def build_modifier(self, request: UpdateDeploymentPolicyRequest) -> DeploymentPolicyModifier:
        """Build DeploymentPolicyModifier from update request."""
        strategy: OptionalState[DeploymentStrategy] = OptionalState.nop()
        strategy_spec: OptionalState[RollingUpdateSpec | BlueGreenSpec] = OptionalState.nop()
        rollback_on_failure: OptionalState[bool] = OptionalState.nop()

        if request.strategy is not None:
            strategy = OptionalState.update(request.strategy)
        if request.rollback_on_failure is not None:
            rollback_on_failure = OptionalState.update(request.rollback_on_failure)
        if request.rolling_update is not None:
            strategy_spec = OptionalState.update(
                RollingUpdateSpec(
                    max_surge=request.rolling_update.max_surge,
                    max_unavailable=request.rolling_update.max_unavailable,
                )
            )
        elif request.blue_green is not None:
            strategy_spec = OptionalState.update(
                BlueGreenSpec(
                    auto_promote=request.blue_green.auto_promote,
                    promote_delay_seconds=request.blue_green.promote_delay_seconds,
                )
            )

        return DeploymentPolicyModifier(
            strategy=strategy,
            strategy_spec=strategy_spec,
            rollback_on_failure=rollback_on_failure,
        )
