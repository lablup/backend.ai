"""
Federated AutoScalingRule (EndpointAutoScalingRuleNode) type with full field definitions for Strawberry GraphQL.
"""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Optional

import strawberry
from strawberry.relay import Node, NodeID


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
