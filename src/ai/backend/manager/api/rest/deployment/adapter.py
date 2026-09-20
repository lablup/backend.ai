"""
Adapters to convert deployment DTOs to repository BatchQuerier objects.
Handles conversion of filter, order, and pagination parameters.
Also provides data-to-DTO conversion functions.
"""

from __future__ import annotations

from typing import assert_never
from uuid import UUID, uuid4

from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.data.filter_specs import UUIDEqualMatchSpec
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.data.model_deployment.types import (
    RouteStatus as CommonRouteStatus,
)
from ai.backend.common.data.model_deployment.types import (
    RouteTrafficStatus as CommonRouteTrafficStatus,
)
from ai.backend.common.dto.manager.deployment import (
    ClusterConfigDTO,
    CreateDeploymentRequest,
    DeploymentDTO,
    DeploymentFilter,
    DeploymentOrder,
    DeploymentPolicyDTO,
    DeploymentStrategyInput,
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
    UpsertDeploymentPolicyRequest,
)
from ai.backend.common.dto.manager.deployment.types import (
    DeploymentOrderField,
    OrderDirection,
    RevisionOrderField,
    RouteOrderField,
)
from ai.backend.common.schema.deployment import BlueGreenSpec, IntOrPercent, RollingUpdateSpec
from ai.backend.common.types import ClusterMode, RuntimeVariant
from ai.backend.manager.data.deployment.creator import (
    DeploymentPolicyConfig,
    ModelRevisionCreator,
    NewDeploymentCreator,
    VFolderMountsCreator,
)
from ai.backend.manager.data.deployment.types import (
    DeploymentMetadata,
    DeploymentNetworkSpec,
    DeploymentPolicyData,
    ExecutionSpec,
    LegacyDeploymentData,
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
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.deployment_policy.upserters import DeploymentPolicyUpserter
from ai.backend.manager.models.deployment_revision.searchable_fields import (
    ModelRevisionSearchableFields,
)
from ai.backend.manager.models.deployment_revision.searchers import ModelRevisionSearcher
from ai.backend.manager.models.endpoint.searchable_fields import DeploymentSearchableFields
from ai.backend.manager.models.routing.cursors import ReplicaCursor
from ai.backend.manager.models.routing.searchable_fields import ReplicaSearchableFields
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.filter_adapter import BaseFilterAdapter

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

    def __init__(
        self,
        *,
        revision_adapter: RevisionAdapter,
        policy_adapter: DeploymentPolicyAdapter,
    ) -> None:
        """Inject the sub-adapters this converter delegates to.

        ``RevisionAdapter`` / ``DeploymentPolicyAdapter`` are the single
        place that knows how to render a revision or policy surface into
        a DTO — recomputing them per call would duplicate that knowledge
        and lose the ability to swap implementations (e.g. testing).
        """
        self._revision_adapter = revision_adapter
        self._policy_adapter = policy_adapter

    def convert_to_dto(
        self,
        data: LegacyDeploymentData,
        runtime_variant_name: RuntimeVariant,
    ) -> DeploymentDTO:
        """Convert LegacyDeploymentData to DTO.

        ``runtime_variant_name`` is resolved by the caller (REST handler)
        from ``data.revision.model_runtime_config.runtime_variant_id``
        via the RuntimeVariant resolver path — the legacy REST response
        preserves the historical name-based field so old clients keep
        seeing the same shape.
        """
        current_revision = None
        if data.revision:
            current_revision = self._revision_adapter.convert_to_dto(
                data.revision, runtime_variant_name
            )

        deployment_policy = None
        if data.policy:
            deployment_policy = self._policy_adapter.convert_to_dto(data.policy)

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
            deployment_policy=deployment_policy,
            sub_step=data.sub_step,
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
        fields = DeploymentSearchableFields.own
        conditions: list[QueryCondition] = [
            *self.apply_string_filter(filter.name, fields.name.filter),
            *self.apply_string_filter(filter.domain_name, fields.domain.filter),
        ]
        if filter.project_id is not None:
            conditions.append(
                fields.project.filter.equals(
                    UUIDEqualMatchSpec(value=filter.project_id, negated=False)
                )
            )
        return conditions

    def _convert_order(self, order: DeploymentOrder) -> QueryOrder:
        """Convert deployment order specification to query order."""
        fields = DeploymentSearchableFields.own
        ascending = order.direction == OrderDirection.ASC
        match order.field:
            case DeploymentOrderField.NAME:
                return fields.name.order.apply(ascending)
            case DeploymentOrderField.CREATED_AT:
                return fields.created_at.order.apply(ascending)
            case DeploymentOrderField.DESTROYED_AT:
                return fields.destroyed_at.order.apply(ascending)
            case DeploymentOrderField.DOMAIN:
                return fields.domain.order.apply(ascending)
            case DeploymentOrderField.PROJECT:
                return fields.project.order.apply(ascending)
            case DeploymentOrderField.RESOURCE_GROUP:
                return fields.resource_group.order.apply(ascending)
            case DeploymentOrderField.TAG:
                return fields.tag.order.apply(ascending)
            case _:
                assert_never(order.field)

    def _build_pagination(self, limit: int, offset: int) -> OffsetPagination:
        """Build pagination from limit and offset."""
        return OffsetPagination(limit=limit, offset=offset)


class RevisionAdapter(BaseFilterAdapter):
    """Adapter for converting revision requests to repository queries."""

    def convert_to_dto(
        self,
        data: ModelRevisionData,
        runtime_variant_name: RuntimeVariant,
    ) -> RevisionDTO:
        """Convert ModelRevisionData to DTO.

        ``runtime_variant_name`` is resolved by the caller (legacy handler)
        from ``data.model_runtime_config.runtime_variant_id`` via the
        RuntimeVariant resolver path; the legacy response DTO carries the
        name-based field so old clients keep seeing the same shape.
        """
        mount_config = data.model_mount_config
        if mount_config.vfolder_id is None:
            raise IncompleteRevisionData(f"Revision {data.id} has incomplete model mount config")
        return RevisionDTO(
            id=data.id,
            cluster_config=ClusterConfigDTO(
                mode=data.cluster_config.mode,
                size=data.cluster_config.size,
            ),
            resource_config=ResourceConfigDTO(
                resource_group_name=data.resource_config.resource_group_name,
                resource_slot=dict(data.resource_config.resource_slot),
            ),
            model_runtime_config=ModelRuntimeConfigDTO(
                runtime_variant=runtime_variant_name,
            ),
            model_mount_config=ModelMountConfigDTO(
                vfolder_id=mount_config.vfolder_id,
                mount_destination=mount_config.mount_destination,
                definition_path=mount_config.definition_path,
            ),
            created_at=data.created_at,
            image_id=data.image_id,
        )

    def build_searcher(self, request: SearchRevisionsRequest) -> ModelRevisionSearcher:
        """The filters and page of a revision search whose deployment the action scopes."""
        conditions = self._convert_filter(request.filter) if request.filter else []
        orders = [self._convert_order(request.order)] if request.order else []
        pagination = self._build_pagination(request.limit, request.offset)

        return ModelRevisionSearcher(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(self, filter: RevisionFilter) -> list[QueryCondition]:
        """Convert revision filter to list of query conditions."""
        fields = ModelRevisionSearchableFields.own
        conditions: list[QueryCondition] = [
            *self.apply_int_filter(filter.revision_number, fields.revision_number.filter),
        ]
        if filter.deployment_id is not None:
            conditions.append(
                fields.deployment_id.filter.equals(
                    UUIDEqualMatchSpec(value=filter.deployment_id, negated=False)
                )
            )
        return conditions

    def _convert_order(self, order: RevisionOrder) -> QueryOrder:
        """Convert revision order specification to query order."""
        fields = ModelRevisionSearchableFields.own
        ascending = order.direction == OrderDirection.ASC
        match order.field:
            case RevisionOrderField.REVISION_NUMBER:
                return fields.revision_number.order.apply(ascending)
            case RevisionOrderField.CREATED_AT:
                return fields.created_at.order.apply(ascending)
            case RevisionOrderField.RESOURCE_GROUP:
                return fields.resource_group.order.apply(ascending)
            case RevisionOrderField.CLUSTER_MODE:
                return fields.cluster_mode.order.apply(ascending)
            case RevisionOrderField.RUNTIME_VARIANT:
                variant = ModelRevisionSearchableFields.nested.runtime_variant
                return variant.correlation.order(variant.fields.name.column).apply(ascending)
            case _:
                assert_never(order.field)

    def _build_pagination(self, limit: int, offset: int) -> OffsetPagination:
        """Build pagination from limit and offset."""
        return OffsetPagination(limit=limit, offset=offset)


class RouteAdapter(BaseFilterAdapter):
    """Adapter for converting route requests to repository queries."""

    def convert_to_dto(self, data: RouteInfo) -> RouteDTO:
        """Convert RouteInfo to DTO."""
        return RouteDTO(
            id=data.route_id,
            endpoint_id=data.deployment_id,
            session_id=str(data.session_id) if data.session_id else None,
            status=CommonRouteStatus(data.status.value),
            traffic_ratio=data.traffic_ratio,
            created_at=data.created_at,
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
            cursor = ReplicaCursor()
            if request.cursor_direction == "forward":
                conditions.append(cursor.after(request.cursor))
            elif request.cursor_direction == "backward":
                conditions.append(cursor.before(request.cursor))

        pagination = self._build_pagination(request.limit, request.offset)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(self, filter: RouteFilter) -> list[QueryCondition]:
        """Convert route filter to list of query conditions."""
        fields = ReplicaSearchableFields.own
        conditions: list[QueryCondition] = []
        if filter.deployment_id is not None:
            conditions.append(
                fields.deployment_id.filter.equals(
                    UUIDEqualMatchSpec(value=filter.deployment_id, negated=False)
                )
            )
        if filter.statuses is not None:
            conditions.append(
                fields.status.filter.in_([ManagerRouteStatus(s.value) for s in filter.statuses])
            )
        if filter.traffic_statuses is not None:
            conditions.append(
                fields.traffic_status.filter.in_([
                    ManagerRouteTrafficStatus(s.value) for s in filter.traffic_statuses
                ])
            )
        return conditions

    def _convert_order(self, order: RouteOrder) -> QueryOrder:
        """Convert route order specification to query order."""
        fields = ReplicaSearchableFields.own
        ascending = order.direction == OrderDirection.ASC
        match order.field:
            case RouteOrderField.CREATED_AT:
                return fields.created_at.order.apply(ascending)
            case RouteOrderField.STATUS:
                return fields.status.order.apply(ascending)
            case RouteOrderField.TRAFFIC_RATIO:
                return fields.traffic_ratio.order.apply(ascending)
            case _:
                assert_never(order.field)

    def _build_pagination(self, limit: int, offset: int) -> OffsetPagination:
        """Build pagination from limit and offset."""
        return OffsetPagination(limit=limit, offset=offset)


def build_revision_creator(
    revision_input: RevisionInput,
    runtime_variant_id: RuntimeVariantID,
) -> ModelRevisionCreator:
    """Build ModelRevisionCreator from RevisionInput.

    Shared by AddRevisionAdapter and CreateDeploymentAdapter to avoid
    duplicated conversion logic. ``runtime_variant_id`` is resolved by
    the caller (legacy REST handler) from the name-based
    ``revision_input.model_runtime_config.runtime_variant`` via the
    RuntimeVariant resolver service; the id flows into the id-typed
    internal chain from here on.
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
                mount_destination=mount.mount_destination,
                mount_perm=mount.mount_perm,
                subpath=mount.subpath,
            )
            for mount in revision_input.extra_mounts
        ]

    mounts = VFolderMountsCreator(
        model_vfolder_id=revision_input.model_mount_config.vfolder_id,
        model_definition_path=revision_input.model_mount_config.definition_path,
        model_mount_destination=revision_input.model_mount_config.mount_destination,
        extra_mounts=extra_mounts,
        # Legacy v1 deployment requests carry no model mount permission;
        # ``None`` adopts the requester's own effective permission.
        model_mount_perm=None,
        vfolder_subpath=revision_input.model_mount_config.subpath,
    )

    execution = ExecutionSpec(
        runtime_variant_id=runtime_variant_id,
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
        model_definition=revision_input.model_definition,
    )


class AddRevisionAdapter:
    """Adapter for converting add revision request to ModelRevisionCreator."""

    @staticmethod
    def build_revision_creator(
        revision_input: RevisionInput,
        runtime_variant_id: RuntimeVariantID,
    ) -> ModelRevisionCreator:
        """Build ModelRevisionCreator from revision input."""
        return build_revision_creator(revision_input, runtime_variant_id)


class CreateDeploymentAdapter:
    """Adapter for converting create deployment request to creators."""

    def build_creator(
        self,
        request: CreateDeploymentRequest,
        user_uuid: UUID,
        runtime_variant_id: RuntimeVariantID,
    ) -> NewDeploymentCreator:
        """
        Convert CreateDeploymentRequest to NewDeploymentCreator.

        ``runtime_variant_id`` is resolved by the caller (legacy handler)
        from the name in ``request.initial_revision.model_runtime_config.runtime_variant``;
        adapter-side flows are id-typed only.
        """
        # Generate name if not provided
        name = request.metadata.name or f"deployment-{uuid4().hex[:8]}"
        tag = ",".join(request.metadata.tags) if request.metadata.tags else None

        # Build metadata
        metadata = DeploymentMetadata(
            name=name,
            domain=request.metadata.domain_name,
            project=request.metadata.project_id,
            resource_group=request.metadata.resource_group_name,
            created_user=user_uuid,
            session_owner=user_uuid,
            created_at=None,
            revision_history_limit=10,
            tag=tag,
        )

        # Build replica spec
        replica_spec = ReplicaSpec(replica_count=request.replica_count)

        # Build network spec
        network = DeploymentNetworkSpec(
            open_to_public=request.network_access.open_to_public,
            preferred_domain_name=request.network_access.preferred_domain_name,
        )

        # Build model revision creator
        model_revision = build_revision_creator(request.initial_revision, runtime_variant_id)

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
        strategy_input: DeploymentStrategyInput,
    ) -> DeploymentPolicyConfig:
        """Build DeploymentPolicyConfig from strategy input."""
        strategy = DeploymentStrategy(strategy_input.type)

        strategy_spec: RollingUpdateSpec | BlueGreenSpec
        match strategy:
            case DeploymentStrategy.ROLLING:
                if strategy_input.rolling_update is None:
                    strategy_spec = RollingUpdateSpec()
                else:
                    strategy_spec = RollingUpdateSpec(
                        max_surge=IntOrPercent(count=strategy_input.rolling_update.max_surge),
                        max_unavailable=IntOrPercent(
                            count=strategy_input.rolling_update.max_unavailable
                        ),
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
        )


class CreateRevisionAdapter:
    """Adapter for converting create revision request to creators."""

    def build_creator(
        self,
        request: RevisionInput,
        runtime_variant_id: RuntimeVariantID,
    ) -> ModelRevisionCreator:
        """
        Convert RevisionInput to ModelRevisionCreator.

        ``runtime_variant_id`` is resolved by the caller (legacy handler)
        from ``request.model_runtime_config.runtime_variant`` name.
        """
        return build_revision_creator(request, runtime_variant_id)


class DeploymentPolicyAdapter:
    """Adapter for converting deployment policy data to DTOs and building specs."""

    def convert_to_dto(self, data: DeploymentPolicyData) -> DeploymentPolicyDTO:
        """Convert DeploymentPolicyData to DTO."""
        return DeploymentPolicyDTO(
            id=data.id,
            deployment_id=data.endpoint,
            strategy=data.strategy,
            strategy_spec=data.strategy_spec.model_dump(),
            created_at=data.created_at,
            updated_at=data.updated_at,
        )

    def build_upserter(self, request: UpsertDeploymentPolicyRequest) -> DeploymentPolicyUpserter:
        """Build the deployment policy upsert spec from the request."""
        strategy = request.strategy

        strategy_spec: RollingUpdateSpec | BlueGreenSpec
        match strategy:
            case DeploymentStrategy.ROLLING:
                if request.rolling_update is not None:
                    strategy_spec = RollingUpdateSpec(
                        max_surge=IntOrPercent(count=request.rolling_update.max_surge),
                        max_unavailable=IntOrPercent(count=request.rolling_update.max_unavailable),
                    )
                else:
                    strategy_spec = RollingUpdateSpec()
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

        return DeploymentPolicyUpserter(
            strategy=strategy,
            strategy_spec=strategy_spec,
        )
