from datetime import datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from typing import Optional
from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import Node, NodeID

from ai.backend.manager.api.gql.types import StrawberryGQLContext


@strawberry.enum(description="Added in 25.1.0")
class AutoScalingMetricSource(StrEnum):
    KERNEL = "KERNEL"
    INFERENCE_FRAMEWORK = "INFERENCE_FRAMEWORK"


@strawberry.type
class AutoScalingRule(Node):
    id: NodeID

    metric_source: AutoScalingMetricSource = strawberry.field(
        description="Added in 25.13.0 (e.g. KERNEL, INFERENCE_FRAMEWORK)"
    )
    metric_name: str = strawberry.field()

    min_threshold: Optional[Decimal] = strawberry.field(
        description="Added in 25.13.0: The minimum threshold for scaling (e.g. 0.5)"
    )
    max_threshold: Optional[Decimal] = strawberry.field(
        description="Added in 25.13.0: The maximum threshold for scaling (e.g. 21.0)"
    )

    step_size: int = strawberry.field(
        description="Added in 25.13.0: The step size for scaling (e.g. 1)."
    )
    time_window: int = strawberry.field(
        description="Added in 25.13.0: The time window (seconds) for scaling (e.g. 60)."
    )

    min_replicas: Optional[int] = strawberry.field(
        description="Added in 25.13.0: The minimum number of replicas (e.g. 1)."
    )
    max_replicas: Optional[int] = strawberry.field(
        description="Added in 25.13.0: The maximum number of replicas (e.g. 10)."
    )

    created_at: datetime
    last_triggered_at: datetime


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


mock_scaling_rule_0 = AutoScalingRule(
    id=UUID("77117a41-87f3-43b7-ba24-40dd5e978720"),
    metric_source=AutoScalingMetricSource.KERNEL,
    metric_name="memory_usage",
    min_threshold=None,
    max_threshold=Decimal("90"),
    step_size=1,
    time_window=120,
    min_replicas=1,
    max_replicas=3,
    created_at=datetime.now() - timedelta(days=15),
    last_triggered_at=datetime.now() - timedelta(hours=6),
)

mock_scaling_rule_1 = AutoScalingRule(
    id=UUID("7ff8c1f5-cf8c-4ea2-911c-24ca0f4c2efb"),
    metric_source=AutoScalingMetricSource.KERNEL,
    metric_name="cpu_usage",
    min_threshold=None,
    max_threshold=Decimal("80"),
    step_size=1,
    time_window=300,
    min_replicas=1,
    max_replicas=5,
    created_at=datetime.now() - timedelta(days=10),
    last_triggered_at=datetime.now() - timedelta(hours=2),
)

mock_scaling_rule_2 = AutoScalingRule(
    id=UUID("483e2158-e089-482b-8cef-260805649cf1"),
    metric_source=AutoScalingMetricSource.INFERENCE_FRAMEWORK,
    metric_name="requests_per_second",
    min_threshold=None,
    max_threshold=Decimal("1000"),
    step_size=2,
    time_window=600,
    min_replicas=2,
    max_replicas=10,
    created_at=datetime.now() - timedelta(days=5),
    last_triggered_at=datetime.now() - timedelta(hours=12),
)


@strawberry.mutation(description="Added in 25.13.0")
async def create_auto_scaling_rule(
    input: CreateAutoScalingRuleInput, info: Info[StrawberryGQLContext]
) -> CreateAutoScalingRulePayload:
    return CreateAutoScalingRulePayload(auto_scaling_rule=mock_scaling_rule_0)


@strawberry.mutation(description="Added in 25.13.0")
async def update_auto_scaling_rule(
    input: UpdateAutoScalingRuleInput, info: Info[StrawberryGQLContext]
) -> UpdateAutoScalingRulePayload:
    return UpdateAutoScalingRulePayload(
        auto_scaling_rule=AutoScalingRule(
            id=input.id,
            metric_source=input.metric_source
            if input.metric_source
            else mock_scaling_rule_1.metric_source,
            metric_name=input.metric_name if input.metric_name else mock_scaling_rule_1.metric_name,
            min_threshold=input.min_threshold
            if input.min_threshold
            else mock_scaling_rule_1.min_threshold,
            max_threshold=input.max_threshold
            if input.max_threshold
            else mock_scaling_rule_1.max_threshold,
            step_size=input.step_size if input.step_size else mock_scaling_rule_1.step_size,
            time_window=input.time_window if input.time_window else mock_scaling_rule_1.time_window,
            min_replicas=input.min_replicas
            if input.min_replicas
            else mock_scaling_rule_1.min_replicas,
            max_replicas=input.max_replicas
            if input.max_replicas
            else mock_scaling_rule_1.max_replicas,
            created_at=datetime.now(),
            last_triggered_at=datetime.now(),
        )
    )


@strawberry.mutation(description="Added in 25.13.0")
async def delete_auto_scaling_rule(
    input: DeleteAutoScalingRuleInput, info: Info[StrawberryGQLContext]
) -> DeleteAutoScalingRulePayload:
    return DeleteAutoScalingRulePayload(id=input.id)
