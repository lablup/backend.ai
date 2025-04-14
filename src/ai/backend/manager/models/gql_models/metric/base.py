from decimal import Decimal
from typing import TYPE_CHECKING, Optional, Self

import graphene

from ai.backend.manager.services.metric.actions.container import (
    ContainerMetricMetadataAction,
)

if TYPE_CHECKING:
    from ...gql import GraphQueryContext


class MetricResultValue(graphene.ObjectType):
    class Meta:
        description = "Added in 25.6.0. A pair of timestamp and value."

    timestamp = graphene.Float()
    value = graphene.String()


class ContainerUtilizationMetricMetadata(graphene.ObjectType):
    class Meta:
        description = "Added in 25.6.0."

    metric_names = graphene.List(graphene.String)

    @classmethod
    async def get_object(
        cls,
        info: graphene.ResolveInfo,
    ) -> Self:
        graph_ctx: GraphQueryContext = info.context
        action_result = await graph_ctx.processors.utilization_metric.query_container_metadata.wait_for_complete(
            ContainerMetricMetadataAction()
        )
        return cls(
            metric_names=action_result.metric_names,
        )


class ContainerUtilizationMetric(graphene.ObjectType):
    class Meta:
        description = "Added in 25.6.0."

    metric_name = graphene.String()
    value_type = graphene.String(description="One of 'current', 'capacity'.")
    values = graphene.List(MetricResultValue)

    max_value = graphene.String(
        description="The maximum value of the metric in given time range. null if no data."
    )
    avg_value = graphene.String(
        description="The average value of the metric in given time range. null if no data."
    )

    async def resolve_max_value(self, info: graphene.ResolveInfo) -> Optional[str]:
        if not self.values:
            return None
        return max(self.values, key=lambda x: Decimal(x.value)).value

    async def resolve_avg_value(self, info: graphene.ResolveInfo) -> Optional[str]:
        if not self.values:
            return None
        avg_val = sum(Decimal(x.value) for x in self.values) / len(self.values)
        return str(avg_val)
