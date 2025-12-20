"""
Adapters to convert deployment DTOs to repository BatchQuerier objects.
Handles conversion of filter, order, and pagination parameters.
Also provides data-to-DTO conversion functions.
"""

from __future__ import annotations

from ai.backend.common.data.model_deployment.types import (
    RouteStatus as CommonRouteStatus,
)
from ai.backend.common.data.model_deployment.types import (
    RouteTrafficStatus as CommonRouteTrafficStatus,
)
from ai.backend.common.dto.manager.deployment import (
    ClusterConfigDTO,
    DeploymentDTO,
    DeploymentFilter,
    DeploymentOrder,
    ModelMountConfigDTO,
    ModelRuntimeConfigDTO,
    NetworkConfigDTO,
    ReplicaStateDTO,
    ResourceConfigDTO,
    RevisionDTO,
    RevisionFilter,
    RevisionOrder,
    RouteDTO,
    RouteFilter,
    RouteOrder,
    SearchDeploymentsRequest,
    SearchRevisionsRequest,
    SearchRoutesRequest,
)
from ai.backend.common.dto.manager.deployment.types import (
    DeploymentOrderField,
    OrderDirection,
    RevisionOrderField,
    RouteOrderField,
)
from ai.backend.manager.api.adapter import BaseFilterAdapter
from ai.backend.manager.data.deployment.types import (
    ModelDeploymentData,
    ModelRevisionData,
    RouteInfo,
)
from ai.backend.manager.data.deployment.types import (
    RouteStatus as ManagerRouteStatus,
)
from ai.backend.manager.data.deployment.types import (
    RouteTrafficStatus as ManagerRouteTrafficStatus,
)
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

__all__ = (
    "DeploymentAdapter",
    "RevisionAdapter",
    "RouteAdapter",
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
                equals_fn=DeploymentConditions.by_name_equals,
                contains_fn=DeploymentConditions.by_name_contains,
            )
            if condition is not None:
                conditions.append(condition)

        # Domain name filter
        if filter.domain_name is not None:
            condition = self.convert_string_filter(
                filter.domain_name,
                equals_fn=DeploymentConditions.by_domain_name_equals,
                contains_fn=DeploymentConditions.by_domain_name_contains,
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
        elif order.field == DeploymentOrderField.CREATED_AT:
            return DeploymentOrders.created_at(ascending=ascending)
        else:
            raise ValueError(f"Unknown order field: {order.field}")

    def _build_pagination(self, limit: int, offset: int) -> OffsetPagination:
        """Build pagination from limit and offset."""
        return OffsetPagination(limit=limit, offset=offset)


class RevisionAdapter(BaseFilterAdapter):
    """Adapter for converting revision requests to repository queries."""

    def convert_to_dto(self, data: ModelRevisionData) -> RevisionDTO:
        """Convert ModelRevisionData to DTO."""
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
                vfolder_id=data.model_mount_config.vfolder_id,
                mount_destination=data.model_mount_config.mount_destination,
                definition_path=data.model_mount_config.definition_path,
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
                equals_fn=RevisionConditions.by_name_equals,
                contains_fn=RevisionConditions.by_name_contains,
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
        elif order.field == RevisionOrderField.CREATED_AT:
            return RevisionOrders.created_at(ascending=ascending)
        else:
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
        elif order.field == RouteOrderField.STATUS:
            return RouteOrders.status(ascending=ascending)
        elif order.field == RouteOrderField.TRAFFIC_RATIO:
            return RouteOrders.traffic_ratio(ascending=ascending)
        else:
            raise ValueError(f"Unknown order field: {order.field}")

    def _build_pagination(self, limit: int, offset: int) -> OffsetPagination:
        """Build pagination from limit and offset."""
        return OffsetPagination(limit=limit, offset=offset)
