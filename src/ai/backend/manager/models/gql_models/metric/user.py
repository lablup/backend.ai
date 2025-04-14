from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Self,
)
from uuid import UUID

import graphene

from ai.backend.manager.services.metric.actions.container import (
    ContainerMetricAction,
)
from ai.backend.manager.services.metric.types import (
    ContainerMetricOptionalLabel,
    MetricQueryParameter,
)

from .base import ContainerUtilizationMetric, MetricResultValue

if TYPE_CHECKING:
    from ...gql import GraphQueryContext


class UserUtilizationMetricQueryInput(graphene.InputObjectType):
    class Meta:
        description = "Added in 25.6.0."

    value_type = graphene.String(
        default_value="current",
        description="One of 'current', 'capacity'. Default value is 'current'.",
    )
    metric_name = graphene.String(
        required=True,
        description="metric name of container utilization. For example, 'cpu_util', 'mem'.",
    )
    start = graphene.String(required=True, description="rfc3339 or unix_timestamp.")
    end = graphene.String(required=True, description="rfc3339 or unix_timestamp.")
    step = graphene.String(
        required=True,
        description=(
            "Query resolution step width in duration format or float number of seconds. "
            "For example, '1m', '1h', '1d', '1w'"
        ),
    )

    def metric_query_param(self) -> MetricQueryParameter:
        return MetricQueryParameter(
            metric_name=self.metric_name,
            value_type=self.value_type,
            start=self.start,
            end=self.end,
            step=self.step,
        )


class UserUtilizationMetric(graphene.ObjectType):
    class Meta:
        description = "Added in 25.6.0."

    user_id = graphene.UUID()
    metrics = graphene.List(ContainerUtilizationMetric)

    @classmethod
    async def get_object(
        cls,
        info: graphene.ResolveInfo,
        user_id: UUID,
        param: MetricQueryParameter,
    ) -> Self:
        graph_ctx: GraphQueryContext = info.context
        action_result = (
            await graph_ctx.processors.utilization_metric.query_container.wait_for_complete(
                ContainerMetricAction(
                    metric_name=param.metric_name,
                    labels=ContainerMetricOptionalLabel(
                        user_id=user_id, value_type=param.value_type
                    ),
                    start=param.start,
                    end=param.end,
                    step=param.step,
                )
            )
        )
        metrics = []
        for result in action_result.result:
            metrics.append(
                ContainerUtilizationMetric(
                    metric_name=param.metric_name,
                    value_type=result.metric.value_type,
                    values=[
                        MetricResultValue(
                            timestamp=value.timestamp,
                            value=value.value,
                        )
                        for value in result.values
                    ],
                )
            )

        return cls(
            user_id=user_id,
            metrics=metrics,
        )
