from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
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

from ...gql_relay import (
    AsyncNode,
)
from .base import MetircResultValue

if TYPE_CHECKING:
    from ...gql import GraphQueryContext


class UserMetricNode(graphene.ObjectType):
    class Meta:
        interfaces = (AsyncNode,)
        description = "Added in 25.5.0."

    user_id = graphene.UUID()
    container_metric_name = graphene.String()
    value_type = graphene.String()
    values = graphene.List(MetircResultValue)

    @classmethod
    async def get_node(
        cls,
        info: graphene.ResolveInfo,
        user_id: UUID,
        param: MetricQueryParameter,
    ) -> Self:
        graph_ctx: GraphQueryContext = info.context
        action_result = await graph_ctx.processors.container_metric.query_metric.wait_for_complete(
            ContainerMetricAction(
                metric_name=param.metric_name,
                value_type=param.value_type,
                labels=ContainerMetricOptionalLabel(user_id=user_id),
                start=param.start,
                end=param.end,
                step=param.step,
            )
        )
        final_result: defaultdict[float, Decimal] = defaultdict(Decimal)  # dict[timestamp, value]
        for result in action_result.result:
            for value in result.values:
                final_result[value.timestamp] += Decimal(value.value)

        return cls(
            user_id=user_id,
            container_metric_name=param.metric_name,
            value_type=param.value_type,
            values=[
                MetircResultValue(
                    timestamp=timestamp,
                    value=str(value),
                )
                for timestamp, value in final_result.items()
            ],
        )
