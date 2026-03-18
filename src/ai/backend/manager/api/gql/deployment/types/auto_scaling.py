"""GraphQL types for auto-scaling rules."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any, Self, override
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.api_handlers import SENTINEL
from ai.backend.common.dto.manager.v2.auto_scaling_rule.request import (
    CreateAutoScalingRuleInput as CreateAutoScalingRuleInputDTO,
)
from ai.backend.common.dto.manager.v2.auto_scaling_rule.request import (
    DeleteAutoScalingRuleInput as DeleteAutoScalingRuleInputDTO,
)
from ai.backend.common.dto.manager.v2.auto_scaling_rule.request import (
    UpdateAutoScalingRuleInput as UpdateAutoScalingRuleInputDTO,
)
from ai.backend.common.types import AutoScalingMetricSource as CommonAutoScalingMetricSource
from ai.backend.manager.api.gql.base import DateTimeFilter, OrderDirection
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy, StrawberryGQLContext
from ai.backend.manager.data.deployment.types import (
    AutoScalingRuleOrderField,
    ModelDeploymentAutoScalingRuleData,
)
from ai.backend.manager.models.endpoint.conditions import AutoScalingRuleConditions
from ai.backend.manager.models.endpoint.orders import AutoScalingRuleOrders
from ai.backend.manager.repositories.base import (
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)


@strawberry.enum(description="Added in 25.1.0")
class AutoScalingMetricSource(StrEnum):
    KERNEL = "KERNEL"
    INFERENCE_FRAMEWORK = "INFERENCE_FRAMEWORK"


@strawberry.input(description="Added in 25.19.0")
class AutoScalingRuleFilter(GQLFilter):
    """Filter for auto-scaling rules."""

    created_at: DateTimeFilter | None = None
    last_triggered_at: DateTimeFilter | None = None

    AND: list[AutoScalingRuleFilter] | None = None
    OR: list[AutoScalingRuleFilter] | None = None
    NOT: list[AutoScalingRuleFilter] | None = None

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

        # Handle AND logical operator
        if self.AND:
            for sub_filter in self.AND:
                conditions.extend(sub_filter.build_conditions())

        # Handle OR logical operator
        if self.OR:
            or_sub_conditions: list[QueryCondition] = []
            for sub_filter in self.OR:
                or_sub_conditions.extend(sub_filter.build_conditions())
            if or_sub_conditions:
                conditions.append(combine_conditions_or(or_sub_conditions))

        # Handle NOT logical operator
        if self.NOT:
            not_sub_conditions: list[QueryCondition] = []
            for sub_filter in self.NOT:
                not_sub_conditions.extend(sub_filter.build_conditions())
            if not_sub_conditions:
                conditions.append(negate_conditions(not_sub_conditions))

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
class AutoScalingRule(PydanticNodeMixin):
    id: NodeID[str]

    metric_source: AutoScalingMetricSource = strawberry.field(
        description="Added in 25.19.0 (e.g. KERNEL, INFERENCE_FRAMEWORK)"
    )
    metric_name: str = strawberry.field()

    min_threshold: Decimal | None = strawberry.field(
        description="Added in 25.19.0: The minimum threshold for scaling (e.g. 0.5)"
    )
    max_threshold: Decimal | None = strawberry.field(
        description="Added in 25.19.0: The maximum threshold for scaling (e.g. 21.0)"
    )

    step_size: int = strawberry.field(
        description="Added in 25.19.0: The step size for scaling (e.g. 1)."
    )
    time_window: int = strawberry.field(
        description="Added in 25.19.0: The time window (seconds) for scaling (e.g. 60)."
    )

    min_replicas: int | None = strawberry.field(
        description="Added in 25.19.0: The minimum number of replicas (e.g. 1)."
    )
    max_replicas: int | None = strawberry.field(
        description="Added in 25.19.0: The maximum number of replicas (e.g. 10)."
    )

    created_at: datetime
    last_triggered_at: datetime

    @classmethod
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.auto_scaling_rule_loader.load_many([
            UUID(nid) for nid in node_ids
        ])
        return [cls.from_dataclass(data) if data is not None else None for data in results]

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

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


# Input Types
@strawberry.experimental.pydantic.input(
    model=CreateAutoScalingRuleInputDTO,
    description="Added in 25.19.0. Input for creating an auto-scaling rule.",
)
class CreateAutoScalingRuleInput:
    model_deployment_id: ID
    metric_source: AutoScalingMetricSource
    metric_name: str
    min_threshold: Decimal | None
    max_threshold: Decimal | None
    step_size: int
    time_window: int
    min_replicas: int | None
    max_replicas: int | None

    def to_pydantic(self) -> CreateAutoScalingRuleInputDTO:
        return CreateAutoScalingRuleInputDTO(
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


@strawberry.experimental.pydantic.input(
    model=UpdateAutoScalingRuleInputDTO,
    description="Added in 25.19.0. Input for updating an auto-scaling rule.",
)
class UpdateAutoScalingRuleInput:
    id: ID
    metric_source: AutoScalingMetricSource | None
    metric_name: str | None
    min_threshold: Decimal | None
    max_threshold: Decimal | None
    step_size: int | None
    time_window: int | None
    min_replicas: int | None
    max_replicas: int | None

    def to_pydantic(self) -> UpdateAutoScalingRuleInputDTO:
        return UpdateAutoScalingRuleInputDTO(
            metric_source=None
            if self.metric_source is None
            else CommonAutoScalingMetricSource(self.metric_source.lower()),
            metric_name=self.metric_name,
            min_threshold=SENTINEL if self.min_threshold is None else self.min_threshold,
            max_threshold=SENTINEL if self.max_threshold is None else self.max_threshold,
            step_size=self.step_size,
            time_window=self.time_window,
            min_replicas=SENTINEL if self.min_replicas is None else self.min_replicas,
            max_replicas=SENTINEL if self.max_replicas is None else self.max_replicas,
        )


@strawberry.experimental.pydantic.input(
    model=DeleteAutoScalingRuleInputDTO,
    description="Added in 25.16.0. Input for deleting an auto-scaling rule",
)
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
