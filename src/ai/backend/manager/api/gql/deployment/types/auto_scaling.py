"""GraphQL types for auto-scaling rules."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Optional, Self, override
from uuid import UUID

import strawberry
from strawberry import ID
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.common.types import AutoScalingMetricSource as CommonAutoScalingMetricSource
from ai.backend.manager.api.gql.base import DateTimeFilter, OrderDirection
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy
from ai.backend.manager.data.deployment.scale import ModelDeploymentAutoScalingRuleCreator
from ai.backend.manager.data.deployment.scale_modifier import ModelDeploymentAutoScalingRuleModifier
from ai.backend.manager.data.deployment.types import (
    AutoScalingRuleOrderField,
    ModelDeploymentAutoScalingRuleData,
)
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder
from ai.backend.manager.repositories.deployment.options import (
    AutoScalingRuleConditions,
    AutoScalingRuleOrders,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.update_auto_scaling_rule import (
    UpdateAutoScalingRuleAction,
)
from ai.backend.manager.types import OptionalState


@strawberry.enum(description="Added in 25.1.0")
class AutoScalingMetricSource(StrEnum):
    KERNEL = "KERNEL"
    INFERENCE_FRAMEWORK = "INFERENCE_FRAMEWORK"


@strawberry.input(description="Added in 25.19.0")
class AutoScalingRuleFilter(GQLFilter):
    """Filter for auto-scaling rules."""

    created_at: Optional[DateTimeFilter] = None
    last_triggered_at: Optional[DateTimeFilter] = None

    @override
    def build_conditions(self) -> list[QueryCondition]:
        """Build query conditions from this filter."""
        conditions: list[QueryCondition] = []

        if self.created_at:
            condition = self.created_at.build_query_condition(
                before_factory=AutoScalingRuleConditions.by_created_at_before,
                after_factory=AutoScalingRuleConditions.by_created_at_after,
                equals_factory=AutoScalingRuleConditions.by_created_at_equals,
            )
            if condition:
                conditions.append(condition)

        if self.last_triggered_at:
            condition = self.last_triggered_at.build_query_condition(
                before_factory=AutoScalingRuleConditions.by_last_triggered_at_before,
                after_factory=AutoScalingRuleConditions.by_last_triggered_at_after,
                equals_factory=AutoScalingRuleConditions.by_last_triggered_at_equals,
            )
            if condition:
                conditions.append(condition)

        return conditions


@strawberry.input(description="Added in 25.19.0")
class AutoScalingRuleOrderBy(GQLOrderBy):
    field: AutoScalingRuleOrderField
    direction: OrderDirection = OrderDirection.DESC

    @override
    def to_query_order(self) -> QueryOrder:
        """Convert to repository QueryOrder."""
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case AutoScalingRuleOrderField.CREATED_AT:
                return AutoScalingRuleOrders.created_at(ascending)


@strawberry.type
class AutoScalingRule(Node):
    id: NodeID[str]

    metric_source: AutoScalingMetricSource = strawberry.field(
        description="Added in 25.19.0 (e.g. KERNEL, INFERENCE_FRAMEWORK)"
    )
    metric_name: str = strawberry.field()

    min_threshold: Optional[Decimal] = strawberry.field(
        description="Added in 25.19.0: The minimum threshold for scaling (e.g. 0.5)"
    )
    max_threshold: Optional[Decimal] = strawberry.field(
        description="Added in 25.19.0: The maximum threshold for scaling (e.g. 21.0)"
    )

    step_size: int = strawberry.field(
        description="Added in 25.19.0: The step size for scaling (e.g. 1)."
    )
    time_window: int = strawberry.field(
        description="Added in 25.19.0: The time window (seconds) for scaling (e.g. 60)."
    )

    min_replicas: Optional[int] = strawberry.field(
        description="Added in 25.19.0: The minimum number of replicas (e.g. 1)."
    )
    max_replicas: Optional[int] = strawberry.field(
        description="Added in 25.19.0: The maximum number of replicas (e.g. 10)."
    )

    created_at: datetime
    last_triggered_at: datetime

    @classmethod
    def from_dataclass(cls, data: ModelDeploymentAutoScalingRuleData) -> Self:
        return cls(
            id=ID(str(data.id)),
            metric_source=AutoScalingMetricSource(data.metric_source.name),
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


AutoScalingRuleEdge = Edge[AutoScalingRule]


@strawberry.type(description="Added in 25.19.0")
class AutoScalingRuleConnection(Connection[AutoScalingRule]):
    count: int

    def __init__(self, *args, count: int, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


# Input Types
@strawberry.input
class CreateAutoScalingRuleInput:
    model_deployment_id: ID
    metric_source: AutoScalingMetricSource
    metric_name: str
    min_threshold: Optional[Decimal]
    max_threshold: Optional[Decimal]
    step_size: int
    time_window: int
    min_replicas: Optional[int]
    max_replicas: Optional[int]

    def to_creator(self) -> ModelDeploymentAutoScalingRuleCreator:
        return ModelDeploymentAutoScalingRuleCreator(
            model_deployment_id=UUID(self.model_deployment_id),
            metric_source=CommonAutoScalingMetricSource(self.metric_source.lower()),
            metric_name=self.metric_name,
            min_threshold=self.min_threshold,
            max_threshold=self.max_threshold,
            step_size=self.step_size,
            time_window=self.time_window,
            min_replicas=self.min_replicas,
            max_replicas=self.max_replicas,
        )


@strawberry.input
class UpdateAutoScalingRuleInput:
    id: ID
    metric_source: Optional[AutoScalingMetricSource]
    metric_name: Optional[str]
    min_threshold: Optional[Decimal]
    max_threshold: Optional[Decimal]
    step_size: Optional[int]
    time_window: Optional[int]
    min_replicas: Optional[int]
    max_replicas: Optional[int]

    def to_action(self) -> UpdateAutoScalingRuleAction:
        optional_state_metric_source = OptionalState[CommonAutoScalingMetricSource].nop()
        if isinstance(self.metric_source, AutoScalingMetricSource):
            optional_state_metric_source = OptionalState[CommonAutoScalingMetricSource].update(
                CommonAutoScalingMetricSource(self.metric_source)
            )
        return UpdateAutoScalingRuleAction(
            auto_scaling_rule_id=UUID(self.id),
            modifier=ModelDeploymentAutoScalingRuleModifier(
                metric_source=optional_state_metric_source,
                metric_name=OptionalState[str].from_graphql(self.metric_name),
                min_threshold=OptionalState[Decimal].from_graphql(self.min_threshold),
                max_threshold=OptionalState[Decimal].from_graphql(self.max_threshold),
                step_size=OptionalState[int].from_graphql(self.step_size),
                time_window=OptionalState[int].from_graphql(self.time_window),
                min_replicas=OptionalState[int].from_graphql(self.min_replicas),
                max_replicas=OptionalState[int].from_graphql(self.max_replicas),
            ),
        )


@strawberry.input
class DeleteAutoScalingRuleInput:
    id: ID


# Payload Types
@strawberry.type
class CreateAutoScalingRulePayload:
    auto_scaling_rule: AutoScalingRule


@strawberry.type
class UpdateAutoScalingRulePayload:
    auto_scaling_rule: AutoScalingRule


@strawberry.type
class DeleteAutoScalingRulePayload:
    id: ID
