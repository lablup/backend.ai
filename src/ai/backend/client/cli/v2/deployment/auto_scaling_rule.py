"""User-facing CLI commands for deployment auto-scaling rules."""

from __future__ import annotations

import asyncio
import sys
import uuid
from decimal import Decimal
from typing import Any

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)


def _run_async(coro_fn: Any) -> None:
    from ai.backend.client.exceptions import BackendAPIError

    try:
        asyncio.run(coro_fn())
    except BackendAPIError as e:
        data = e.args[2] if len(e.args) > 2 else {}
        title = data.get("title", "") if isinstance(data, dict) else ""
        msg = data.get("msg", "") if isinstance(data, dict) else ""
        status = e.args[0] if e.args else "?"
        detail = title or msg or str(e)
        click.echo(f"Error ({status}): {detail}", err=True)
        sys.exit(1)


@click.group(name="auto-scaling-rule")
def auto_scaling_rule() -> None:
    """Deployment auto-scaling rule commands."""


@auto_scaling_rule.command()
@click.option(
    "--deployment-id", required=True, type=click.UUID, help="Deployment UUID to attach the rule to."
)
@click.option(
    "--metric-source",
    required=True,
    type=click.Choice(["KERNEL", "INFERENCE_FRAMEWORK"], case_sensitive=False),
    help="Source of the metric.",
)
@click.option("--metric-name", required=True, type=str, help="Name of the metric to monitor.")
@click.option("--step-size", required=True, type=int, help="Scale step size (>= 1).")
@click.option(
    "--time-window", required=True, type=int, help="Time window in seconds for evaluation (>= 1)."
)
@click.option("--min-threshold", default=None, type=str, help="Minimum threshold for scaling.")
@click.option("--max-threshold", default=None, type=str, help="Maximum threshold for scaling.")
@click.option("--min-replicas", default=None, type=int, help="Minimum number of replicas.")
@click.option("--max-replicas", default=None, type=int, help="Maximum number of replicas.")
def create(
    deployment_id: uuid.UUID,
    metric_source: str,
    metric_name: str,
    step_size: int,
    time_window: int,
    min_threshold: str | None,
    max_threshold: str | None,
    min_replicas: int | None,
    max_replicas: int | None,
) -> None:
    """Create an auto-scaling rule for a deployment."""
    from ai.backend.common.dto.manager.v2.auto_scaling_rule.request import (
        CreateAutoScalingRuleInput,
    )
    from ai.backend.common.dto.manager.v2.auto_scaling_rule.types import AutoScalingMetricSource

    body = CreateAutoScalingRuleInput(
        model_deployment_id=deployment_id,
        metric_source=AutoScalingMetricSource(metric_source.upper()),
        metric_name=metric_name,
        step_size=step_size,
        time_window=time_window,
        min_threshold=Decimal(min_threshold) if min_threshold is not None else None,
        max_threshold=Decimal(max_threshold) if max_threshold is not None else None,
        min_replicas=min_replicas,
        max_replicas=max_replicas,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.deployment.create_auto_scaling_rule(body)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@auto_scaling_rule.command()
@click.argument("deployment_id", type=click.UUID)
@click.option("--limit", type=int, default=20, help="Maximum number of items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., created_at:desc).",
)
def search(
    deployment_id: uuid.UUID,
    limit: int,
    offset: int,
    order_by: tuple[str, ...],
) -> None:
    """Search auto-scaling rules for a deployment."""
    from ai.backend.common.dto.manager.v2.auto_scaling_rule.request import (
        AutoScalingRuleFilter,
        AutoScalingRuleOrder,
        SearchAutoScalingRulesInput,
    )
    from ai.backend.common.dto.manager.v2.auto_scaling_rule.types import (
        AutoScalingRuleOrderField,
    )

    filter_dto = AutoScalingRuleFilter(model_deployment_id=deployment_id)
    orders = (
        parse_order_options(order_by, AutoScalingRuleOrderField, AutoScalingRuleOrder)
        if order_by
        else None
    )

    body = SearchAutoScalingRulesInput(
        filter=filter_dto,
        order=orders,
        limit=limit,
        offset=offset,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.deployment.search_auto_scaling_rules(deployment_id, body)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@auto_scaling_rule.command()
@click.argument("rule_id", type=click.UUID)
def get(rule_id: uuid.UUID) -> None:
    """Get an auto-scaling rule by ID."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.deployment.get_auto_scaling_rule(rule_id)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@auto_scaling_rule.command()
@click.argument("rule_id", type=click.UUID)
@click.option(
    "--metric-source",
    default=None,
    type=click.Choice(["KERNEL", "INFERENCE_FRAMEWORK"], case_sensitive=False),
    help="Updated metric source.",
)
@click.option("--metric-name", default=None, type=str, help="Updated metric name.")
@click.option("--step-size", default=None, type=int, help="Updated scale step size.")
@click.option("--time-window", default=None, type=int, help="Updated time window in seconds.")
@click.option("--min-threshold", default=None, type=str, help="Updated minimum threshold.")
@click.option("--max-threshold", default=None, type=str, help="Updated maximum threshold.")
@click.option("--min-replicas", default=None, type=int, help="Updated minimum replicas.")
@click.option("--max-replicas", default=None, type=int, help="Updated maximum replicas.")
def update(
    rule_id: uuid.UUID,
    metric_source: str | None,
    metric_name: str | None,
    step_size: int | None,
    time_window: int | None,
    min_threshold: str | None,
    max_threshold: str | None,
    min_replicas: int | None,
    max_replicas: int | None,
) -> None:
    """Update an auto-scaling rule."""
    from ai.backend.common.dto.manager.v2.auto_scaling_rule.request import (
        UpdateAutoScalingRuleInput,
    )
    from ai.backend.common.dto.manager.v2.auto_scaling_rule.types import AutoScalingMetricSource

    body = UpdateAutoScalingRuleInput(
        id=rule_id,
        metric_source=(
            AutoScalingMetricSource(metric_source.upper()) if metric_source is not None else None
        ),
        metric_name=metric_name,
        step_size=step_size,
        time_window=time_window,
        min_threshold=Decimal(min_threshold) if min_threshold is not None else None,
        max_threshold=Decimal(max_threshold) if max_threshold is not None else None,
        min_replicas=min_replicas if min_replicas is not None else None,
        max_replicas=max_replicas if max_replicas is not None else None,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.deployment.update_auto_scaling_rule(rule_id, body)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@auto_scaling_rule.command()
@click.argument("rule_id", type=click.UUID)
def delete(rule_id: uuid.UUID) -> None:
    """Delete an auto-scaling rule."""
    from ai.backend.common.dto.manager.v2.auto_scaling_rule.request import (
        DeleteAutoScalingRuleInput,
    )

    body = DeleteAutoScalingRuleInput(id=rule_id)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.deployment.delete_auto_scaling_rule(body)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@auto_scaling_rule.command(name="bulk-delete")
@click.argument("rule_ids", nargs=-1, required=True, type=click.UUID)
def bulk_delete(rule_ids: tuple[uuid.UUID, ...]) -> None:
    """Bulk delete auto-scaling rules."""
    from ai.backend.common.dto.manager.v2.auto_scaling_rule.request import (
        BulkDeleteAutoScalingRulesInput,
    )

    body = BulkDeleteAutoScalingRulesInput(ids=list(rule_ids))

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.deployment.bulk_delete_auto_scaling_rules(body)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)
