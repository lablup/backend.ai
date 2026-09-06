from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Self,
)
from uuid import UUID

import graphene

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.dto.clients.prometheus.request import QueryTimeRange
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.clients.prometheus.metric_types import (
    ContainerMetricOptionalLabel,
    ContainerMetricResult,
)
from ai.backend.manager.services.metric.actions.search_container_metrics import (
    GlobalSearchContainerMetricsAction,
)
from ai.backend.manager.services.metric.actions.search_user_container_metrics import (
    SearchUserContainerMetricsAction,
)
from ai.backend.manager.services.metric.types import (
    MetricQueryParameter,
)

from .base import ContainerUtilizationMetric, MetricResultValue

if TYPE_CHECKING:
    from ai.backend.manager.api.gql_legacy.schema import GraphQueryContext


class UserUtilizationMetricQueryInput(graphene.InputObjectType):  # type: ignore[misc]
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


class UserUtilizationMetric(graphene.ObjectType):  # type: ignore[misc]
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
        results = await cls._query(graph_ctx, user_id, param)
        metrics = []
        for result in results:
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

    @classmethod
    async def _query(
        cls,
        graph_ctx: GraphQueryContext,
        user_id: UUID,
        param: MetricQueryParameter,
    ) -> list[ContainerMetricResult]:
        """Read the metric as the acting user, or across users when it names another.

        Which action runs is what gates the read: their own metrics are answered for
        them, anyone else's reaches every user and stays behind the global gate.
        """
        acting = current_user()
        if acting is None:
            raise UnreachableError("Acting user is not set in the request context")
        time_range = QueryTimeRange(start=param.start, end=param.end, step=param.step)
        if acting.user_id == user_id:
            own = await graph_ctx.processors.metric.search_user_container_metrics.run(
                SearchUserContainerMetricsAction(
                    user_id=UserID(user_id),
                    metric_name=param.metric_name,
                    value_type=param.value_type,
                    time_range=time_range,
                )
            )
            return own.result
        across = await graph_ctx.processors.metric.global_search.run(
            GlobalSearchContainerMetricsAction(
                metric_name=param.metric_name,
                labels=ContainerMetricOptionalLabel(user_id=user_id, value_type=param.value_type),
                time_range=time_range,
            )
        )
        return across.result
