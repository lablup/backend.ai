import textwrap
from collections.abc import Sequence
from decimal import Decimal
from typing import Any, Optional, Self
from uuid import UUID

from ai.backend.common.types import AutoScalingMetricComparator, AutoScalingMetricSource

from ...cli.types import Undefined, undefined
from ..output.fields import service_auto_scaling_rule_fields
from ..output.types import FieldSpec, RelayPaginatedResult
from ..pagination import execute_paginated_relay_query
from ..session import api_session
from ..types import set_if_set
from .base import BaseFunction, api_function

_default_fields: Sequence[FieldSpec] = (
    service_auto_scaling_rule_fields["id"],
    service_auto_scaling_rule_fields["metric_source"],
    service_auto_scaling_rule_fields["metric_name"],
    service_auto_scaling_rule_fields["comparator"],
    service_auto_scaling_rule_fields["threshold"],
    service_auto_scaling_rule_fields["endpoint"],
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
                "endpoint": (str(endpoint_id), "String!"),
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
    ) -> Self:
        q = textwrap.dedent(
            """
            mutation(
                $endpoint: String!,
                $metric_source: AutoScalingMetricSource!,
                $metric_name: String!,
                $threshold: String!,
                $comparator: AutoScalingMetricComparator!,
                $step_size: Int!,
                $cooldown_seconds: Int!,
                $min_replicas: Int,
                $max_replicas: Int
            ) {
                create_endpoint_auto_scaling_rule_node(
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

        return cls(rule_id=UUID(data["create_endpoint_auto_scaling_rule_node"]["rule"]["row_id"]))

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
            query($rule_id: String!) {
                endpoint_auto_scaling_rule_node(id: $rule_id) {$fields}
            }
        """
        )
        query = query.replace("$fields", " ".join(f.field_ref for f in (fields or _default_fields)))
        variables = {"rule_id": str(self.rule_id)}
        data = await api_session.get().Admin._query(query, variables)
        return data["endpoint_auto_scaling_rule_node"]

    @api_function
    async def update(
        self,
        *,
        metric_source: AutoScalingMetricSource | Undefined = undefined,
        metric_name: str | Undefined = undefined,
        threshold: Decimal | Undefined = undefined,
        comparator: AutoScalingMetricComparator | Undefined = undefined,
        step_size: int | Undefined = undefined,
        cooldown_seconds: int | Undefined = undefined,
        min_replicas: Optional[int] | Undefined = undefined,
        max_replicas: Optional[int] | Undefined = undefined,
    ) -> Self:
        q = textwrap.dedent(
            """
            mutation(
                $rule_id: String!,
                $input: ModifyEndpointAutoScalingRuleInput!,
            ) {
                modify_endpoint_auto_scaling_rule_node(
                    id: $rule_id,
                    props: $input
                ) {
                    ok
                    msg
                }
            }
            """
        )
        inputs: dict[str, Any] = {}
        set_if_set(inputs, "metric_source", metric_source)
        set_if_set(inputs, "metric_name", metric_name)
        set_if_set(inputs, "threshold", threshold)
        set_if_set(inputs, "comparator", comparator)
        set_if_set(inputs, "step_size", step_size)
        set_if_set(inputs, "cooldown_seconds", cooldown_seconds)
        set_if_set(inputs, "min_replicas", min_replicas)
        set_if_set(inputs, "max_replicas", max_replicas)
        data = await api_session.get().Admin._query(
            q,
            {"rule_id": str(self.rule_id), "input": inputs},
        )

        return data["modify_endpoint_auto_scaling_rule_node"]

    @api_function
    async def delete(self) -> None:
        q = textwrap.dedent(
            """
            mutation($rule_id: String!) {
                delete_endpoint_auto_scaling_rule_node(id: $rule_id) {
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
        return data["delete_endpoint_auto_scaling_rule_node"]
