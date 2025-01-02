import textwrap
from decimal import Decimal
from typing import Optional, Sequence
from uuid import UUID

from ai.backend.client.func.base import BaseFunction, api_function
from ai.backend.client.output.types import FieldSpec, RelayPaginatedResult
from ai.backend.client.pagination import execute_paginated_relay_query
from ai.backend.client.session import api_session
from ai.backend.common.types import AutoScalingMetricComparator, AutoScalingMetricSource

from ..output.fields import service_auto_scaling_rule_fields

_default_fields: Sequence[FieldSpec] = (
    service_auto_scaling_rule_fields["id"],
    service_auto_scaling_rule_fields["metric_source"],
    service_auto_scaling_rule_fields["metric_name"],
    service_auto_scaling_rule_fields["comparator"],
    service_auto_scaling_rule_fields["threshold"],
    service_auto_scaling_rule_fields["endpoint"],
    service_auto_scaling_rule_fields["comparator"],
    service_auto_scaling_rule_fields["step_size"],
    service_auto_scaling_rule_fields["cooldown_seconds"],
    service_auto_scaling_rule_fields["min_replicas"],
    service_auto_scaling_rule_fields["max_replicas"],
    service_auto_scaling_rule_fields["created_at"],
    service_auto_scaling_rule_fields["last_triggered_at"],
)


class ServiceAutoScalingRule(BaseFunction):
    rule_id: UUID

    @api_function
    @classmethod
    async def paginated_list(
        cls,
        endpoint_id: UUID,
        *,
        fields: Sequence[FieldSpec] | None = None,
        page_offset: int = 0,
        page_size: int = 20,
        filter: Optional[str] = None,
        order: Optional[str] = None,
    ) -> RelayPaginatedResult[dict]:
        return await execute_paginated_relay_query(
            "endpoint_auto_scaling_rule_nodes",
            {
                "endpoint": (str(endpoint_id), "String"),
                "filter": (filter, "String"),
                "order": (order, "String"),
            },
            fields or _default_fields,
            limit=page_size,
            offset=page_offset,
        )

    @api_function
    @classmethod
    async def create(
        cls,
        service: UUID,
        metric_source: AutoScalingMetricSource,
        metric_name: str,
        threshold: Decimal,
        comparator: AutoScalingMetricComparator,
        step_size: int,
        cooldown_seconds: int,
        *,
        min_replicas: Optional[int] = None,
        max_replicas: Optional[int] = None,
    ) -> "ServiceAutoScalingRule":
        q = textwrap.dedent(
            """
            mutation(
                $endpoint: String!,
                $metric_source: String!,
                $metric_name: String!,
                $threshold: String!,
                $comparator: String!,
                $step_size: Int!,
                $cooldown_seconds: Int!,
                $min_replicas: Int,
                $max_replicas: Int
            ) {
                create_endpoint_auto_scaling_rule(
                    endpoint: $endpoint,
                    props: {
                        metric_source: $metric_source,
                        metric_name: $metric_name,
                        threshold: $threshold,
                        comparator: $comparator,
                        step_size: $step_size,
                        cooldown_seconds: $cooldown_seconds,
                        min_replicas: $min_replicas,
                        max_replicas: $max_replicas
                    }
                ) {
                    rule {
                        row_id
                    }
                }
            }
            """
        )
        data = await api_session.get().Admin._query(
            q,
            {
                "endpoint": str(service),
                "metric_source": metric_source,
                "metric_name": metric_name,
                "threshold": threshold,
                "comparator": comparator,
                "step_size": step_size,
                "cooldown_seconds": cooldown_seconds,
                "min_replicas": min_replicas,
                "max_replicas": max_replicas,
            },
        )

        return cls(rule_id=UUID(data["create_endpoint_auto_scaling_rule"]["rule"]["row_id"]))

    def __init__(self, rule_id: UUID) -> None:
        super().__init__()
        self.rule_id = rule_id

    @api_function
    async def get(
        self,
        fields: Sequence[FieldSpec] | None = None,
    ) -> Sequence[dict]:
        query = textwrap.dedent(
            """\
            query($rule_id: UUID!) {
                endpoint_auto_scaling_rule_node(rule_id: $rule_id) {$fields}
            }
        """
        )
        query = query.replace("$fields", " ".join(f.field_ref for f in (fields or _default_fields)))
        variables = {"rule_id": self.rule_id}
        data = await api_session.get().Admin._query(query, variables)
        return data["endpoint"]

    @api_function
    async def update(
        self,
        *,
        metric_source: Optional[AutoScalingMetricSource] = None,
        metric_name: Optional[str] = None,
        threshold: Optional[Decimal] = None,
        comparator: Optional[AutoScalingMetricComparator] = None,
        step_size: Optional[int] = None,
        cooldown_seconds: Optional[int] = None,
        min_replicas: Optional[int] = None,
        max_replicas: Optional[int] = None,
    ) -> "ServiceAutoScalingRule":
        q = textwrap.dedent(
            """
            mutation(
                $rule_id: String!,
                $metric_source: String,
                $metric_name: String,
                $threshold: String,
                $comparator: String,
                $step_size: Int,
                $cooldown_seconds: Int,
                $min_replicas: Int,
                $max_replicas: Int
            ) {
                modify_endpoint_auto_scaling_rule(
                    id: $rule_id,
                    props: {
                        metric_source: $metric_source,
                        metric_name: $metric_name,
                        threshold: $threshold,
                        comparator: $comparator,
                        step_size: $step_size,
                        cooldown_seconds: $cooldown_seconds,
                        min_replicas: $min_replicas,
                        max_replicas: $max_replicas
                    }
                ) {
                    rule {
                        ok
                        msg
                    }
                }
            }
            """
        )
        data = await api_session.get().Admin._query(
            q,
            {
                "rule_id": str(self.rule_id),
                "metric_source": metric_source,
                "metric_name": metric_name,
                "threshold": threshold,
                "comparator": comparator,
                "step_size": step_size,
                "cooldown_seconds": cooldown_seconds,
                "min_replicas": min_replicas,
                "max_replicas": max_replicas,
            },
        )

        return data["modify_endpoint_auto_scaling_rule"]

    @api_function
    async def delete(self) -> None:
        q = textwrap.dedent(
            """
            mutation($rule_id: String!) {
                delete_endpoint_auto_scaling_rule(id: $rule_id) {
                    ok
                    msg
                }
            }
            """
        )

        variables = {
            "rule_id": str(self.rule_id),
        }
        data = await api_session.get().Admin._query(q, variables)
        return data["delete_endpoint_auto_scaling_rule"]
