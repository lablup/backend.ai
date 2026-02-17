"""
Adapters to convert auto-scaling rule DTOs to repository query objects.
Handles conversion of filter, order, and pagination parameters.
Also provides data-to-DTO conversion functions.
"""

from __future__ import annotations

from decimal import Decimal

from ai.backend.common.dto.manager.auto_scaling_rule import (
    AutoScalingRuleDTO,
    AutoScalingRuleFilter,
    AutoScalingRuleOrder,
    AutoScalingRuleOrderField,
    OrderDirection,
    SearchAutoScalingRulesRequest,
    UpdateAutoScalingRuleRequest,
)
from ai.backend.common.types import AutoScalingMetricSource
from ai.backend.manager.api.adapter import BaseFilterAdapter
from ai.backend.manager.data.deployment.scale_modifier import ModelDeploymentAutoScalingRuleModifier
from ai.backend.manager.data.deployment.types import ModelDeploymentAutoScalingRuleData
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.repositories.deployment.options import (
    AutoScalingRuleConditions,
    AutoScalingRuleOrders,
)
from ai.backend.manager.types import OptionalState

__all__ = ("AutoScalingRuleAdapter",)


class AutoScalingRuleAdapter(BaseFilterAdapter):
    """Adapter for converting auto-scaling rule requests to repository queries."""

    def convert_to_dto(self, data: ModelDeploymentAutoScalingRuleData) -> AutoScalingRuleDTO:
        """Convert ModelDeploymentAutoScalingRuleData to DTO."""
        return AutoScalingRuleDTO(
            id=data.id,
            model_deployment_id=data.model_deployment_id,
            metric_source=data.metric_source,
            metric_name=data.metric_name,
            min_threshold=data.min_threshold,
            max_threshold=data.max_threshold,
            step_size=data.step_size,
            time_window=data.time_window,
            min_replicas=data.min_replicas,
            max_replicas=data.max_replicas,
            created_at=data.created_at,
            last_triggered_at=data.last_triggered_at,
        )

    def build_modifier(
        self, request: UpdateAutoScalingRuleRequest
    ) -> ModelDeploymentAutoScalingRuleModifier:
        """Convert update request to modifier."""
        metric_source = OptionalState[AutoScalingMetricSource].nop()
        metric_name = OptionalState[str].nop()
        min_threshold: OptionalState[Decimal] = OptionalState.nop()
        max_threshold: OptionalState[Decimal] = OptionalState.nop()
        step_size = OptionalState[int].nop()
        time_window = OptionalState[int].nop()
        min_replicas = OptionalState[int].nop()
        max_replicas = OptionalState[int].nop()

        if request.metric_source is not None:
            metric_source = OptionalState.update(request.metric_source)
        if request.metric_name is not None:
            metric_name = OptionalState.update(request.metric_name)
        if request.min_threshold is not None:
            min_threshold = OptionalState.update(request.min_threshold)
        if request.max_threshold is not None:
            max_threshold = OptionalState.update(request.max_threshold)
        if request.step_size is not None:
            step_size = OptionalState.update(request.step_size)
        if request.time_window is not None:
            time_window = OptionalState.update(request.time_window)
        if request.min_replicas is not None:
            min_replicas = OptionalState.update(request.min_replicas)
        if request.max_replicas is not None:
            max_replicas = OptionalState.update(request.max_replicas)

        return ModelDeploymentAutoScalingRuleModifier(
            metric_source=metric_source,
            metric_name=metric_name,
            min_threshold=min_threshold,
            max_threshold=max_threshold,
            step_size=step_size,
            time_window=time_window,
            min_replicas=min_replicas,
            max_replicas=max_replicas,
        )

    def build_querier(self, request: SearchAutoScalingRulesRequest) -> BatchQuerier:
        """Build a BatchQuerier for auto-scaling rules from search request."""
        conditions = self._convert_filter(request.filter) if request.filter else []
        orders = [self._convert_order(o) for o in request.order] if request.order else []
        pagination = self._build_pagination(request.limit, request.offset)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(self, filter: AutoScalingRuleFilter) -> list[QueryCondition]:
        """Convert auto-scaling rule filter to list of query conditions."""
        conditions: list[QueryCondition] = []

        if filter.model_deployment_id is not None:
            conditions.append(
                AutoScalingRuleConditions.by_deployment_id(filter.model_deployment_id)
            )

        return conditions

    def _convert_order(self, order: AutoScalingRuleOrder) -> QueryOrder:
        """Convert auto-scaling rule order specification to query order."""
        ascending = order.direction == OrderDirection.ASC

        if order.field == AutoScalingRuleOrderField.CREATED_AT:
            return AutoScalingRuleOrders.created_at(ascending=ascending)
        raise ValueError(f"Unknown order field: {order.field}")

    def _build_pagination(self, limit: int, offset: int) -> OffsetPagination:
        """Build pagination from limit and offset."""
        return OffsetPagination(limit=limit, offset=offset)
