"""GraphQL types for auto-scaling rules."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any, Self, cast
from uuid import UUID

from strawberry import ID, UNSET, Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.auto_scaling_rule.request import (
    CreateAutoScalingRuleInput as CreateAutoScalingRuleInputDTO,
)
from ai.backend.common.dto.manager.v2.auto_scaling_rule.request import (
    DeleteAutoScalingRuleInput as DeleteAutoScalingRuleInputDTO,
)
from ai.backend.common.dto.manager.v2.auto_scaling_rule.request import (
    UpdateAutoScalingRuleInput as UpdateAutoScalingRuleInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    AutoScalingRuleFilter as AutoScalingRuleFilterDTO,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    AutoScalingRuleOrder as AutoScalingRuleOrderDTO,
)
from ai.backend.common.dto.manager.v2.deployment.response import (
    AutoScalingRuleNode as AutoScalingRuleNodeDTO,
)
from ai.backend.common.dto.manager.v2.deployment.response import (
    CreateAutoScalingRulePayload as CreateAutoScalingRulePayloadDTO,
)
from ai.backend.common.dto.manager.v2.deployment.response import (
    DeleteAutoScalingRulePayload as DeleteAutoScalingRulePayloadDTO,
)
from ai.backend.common.dto.manager.v2.deployment.response import (
    UpdateAutoScalingRulePayload as UpdateAutoScalingRulePayloadDTO,
)
from ai.backend.common.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import DateTimeFilter, OrderDirection
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_added_field,
    gql_connection_type,
    gql_enum,
    gql_field,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.data.deployment.types import (
    AutoScalingRuleOrderField,
)


@gql_enum(
    BackendAIGQLMeta(added_version="25.1.0", description="Metric source for auto-scaling rules")
)
class AutoScalingMetricSource(StrEnum):
    KERNEL = "KERNEL"
    INFERENCE_FRAMEWORK = "INFERENCE_FRAMEWORK"
    PROMETHEUS = "PROMETHEUS"


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.19.0"),
    name="AutoScalingRuleFilter",
)
class AutoScalingRuleFilter(PydanticInputMixin[AutoScalingRuleFilterDTO]):
    """Filter for auto-scaling rules."""

    created_at: DateTimeFilter | None = None
    last_triggered_at: DateTimeFilter | None = None

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.19.0"),
)
class AutoScalingRuleOrderBy(PydanticInputMixin[AutoScalingRuleOrderDTO]):
    field: AutoScalingRuleOrderField
    direction: OrderDirection = OrderDirection.DESC


@gql_node_type(
    BackendAIGQLMeta(
        added_version="25.19.0", description="An auto-scaling rule for a model deployment."
    )
)
class AutoScalingRule(PydanticNodeMixin[AutoScalingRuleNodeDTO]):
    id: NodeID[str]

    metric_source: AutoScalingMetricSource = gql_field(
        description="The source of the scaling metric (e.g. KERNEL, INFERENCE_FRAMEWORK)."
    )
    metric_name: str = gql_field(description="The metric name field.")

    min_threshold: Decimal | None = gql_field(
        description="The minimum threshold for scaling (e.g. 0.5)."
    )
    max_threshold: Decimal | None = gql_field(
        description="The maximum threshold for scaling (e.g. 21.0)."
    )

    step_size: int = gql_field(description="The step size for scaling (e.g. 1).")
    time_window: int = gql_field(description="The time window in seconds for scaling (e.g. 60).")

    min_replicas: int | None = gql_field(description="The minimum number of replicas (e.g. 1).")
    max_replicas: int | None = gql_field(description="The maximum number of replicas (e.g. 10).")

    prometheus_query_preset_id: ID | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="The Prometheus query preset ID for PROMETHEUS metric source.",
        ),
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
        return cast(list[Self | None], results)


AutoScalingRuleEdge = Edge[AutoScalingRule]


@gql_connection_type(
    BackendAIGQLMeta(added_version="25.19.0", description="Connection for auto-scaling rules.")
)
class AutoScalingRuleConnection(Connection[AutoScalingRule]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


# Input Types
@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for creating an auto-scaling rule.", added_version="25.19.0"
    ),
)
class CreateAutoScalingRuleInput(PydanticInputMixin[CreateAutoScalingRuleInputDTO]):
    model_deployment_id: ID
    metric_source: AutoScalingMetricSource
    metric_name: str
    min_threshold: Decimal | None
    max_threshold: Decimal | None
    step_size: int
    time_window: int
    min_replicas: int | None
    max_replicas: int | None
    prometheus_query_preset_id: ID | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for updating an auto-scaling rule.",
        added_version="25.19.0",
    ),
    name="UpdateAutoScalingRuleInput",
)
class UpdateAutoScalingRuleInput(PydanticInputMixin[UpdateAutoScalingRuleInputDTO]):
    id: ID
    metric_source: AutoScalingMetricSource | None = UNSET
    metric_name: str | None = UNSET
    min_threshold: Decimal | None = UNSET
    max_threshold: Decimal | None = UNSET
    step_size: int | None = UNSET
    time_window: int | None = UNSET
    min_replicas: int | None = UNSET
    max_replicas: int | None = UNSET
    prometheus_query_preset_id: ID | None = UNSET


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for deleting an auto-scaling rule", added_version="25.16.0"
    ),
)
class DeleteAutoScalingRuleInput(PydanticInputMixin[DeleteAutoScalingRuleInputDTO]):
    id: ID


# Payload Types
@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.19.0", description="Payload for creating an auto-scaling rule."
    ),
    model=CreateAutoScalingRulePayloadDTO,
)
class CreateAutoScalingRulePayload:
    rule: AutoScalingRule


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.19.0", description="Payload for updating an auto-scaling rule."
    ),
    model=UpdateAutoScalingRulePayloadDTO,
)
class UpdateAutoScalingRulePayload:
    rule: AutoScalingRule


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.19.0", description="Payload for deleting an auto-scaling rule."
    ),
    model=DeleteAutoScalingRulePayloadDTO,
)
class DeleteAutoScalingRulePayload:
    id: ID
