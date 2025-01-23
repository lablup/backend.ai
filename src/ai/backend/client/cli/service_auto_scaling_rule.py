import decimal
import sys
from typing import Any, Iterable, Optional
from uuid import UUID

import click

from ai.backend.cli.params import OptionalType
from ai.backend.cli.types import ExitCode, Undefined, undefined
from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.service import get_service_id
from ai.backend.client.cli.types import CLIContext
from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.session import Session
from ai.backend.common.types import AutoScalingMetricComparator, AutoScalingMetricSource

from ..func.service_auto_scaling_rule import _default_fields as _default_get_fields
from ..output.fields import service_auto_scaling_rule_fields
from .pretty import print_done
from .service import service

_default_list_fields = (
    service_auto_scaling_rule_fields["id"],
    service_auto_scaling_rule_fields["metric_source"],
    service_auto_scaling_rule_fields["metric_name"],
    service_auto_scaling_rule_fields["comparator"],
    service_auto_scaling_rule_fields["threshold"],
)


@service.group()
def auto_scaling_rule() -> None:
    """Set of model service auto-scaling rule operations"""


@auto_scaling_rule.command()
@pass_ctx_obj
@click.argument("service", type=str, metavar="SERVICE_NAME_OR_ID")
@click.option(
    "--metric-source",
    type=click.Choice([*AutoScalingMetricSource], case_sensitive=False),
    required=True,
)
@click.option("--metric-name", type=str, required=True)
@click.option("--threshold", type=str, required=True)
@click.option(
    "--comparator",
    type=click.Choice([*AutoScalingMetricComparator], case_sensitive=False),
    required=True,
)
@click.option("--step-size", type=int, required=True)
@click.option("--cooldown-seconds", type=int, required=True)
@click.option("--min-replicas", type=int)
@click.option("--max-replicas", type=int)
def create(
    ctx: CLIContext,
    service: str,
    *,
    metric_source: AutoScalingMetricSource,
    metric_name: str,
    threshold: str,
    comparator: AutoScalingMetricComparator,
    step_size: int,
    cooldown_seconds: int,
    min_replicas: Optional[int] = None,
    max_replicas: Optional[int] = None,
) -> None:
    """Create a new auto-scaling rule."""

    with Session() as session:
        try:
            _threshold = decimal.Decimal(threshold)
        except decimal.InvalidOperation:
            ctx.output.print_fail(f"{threshold} is not a valid Decimal")
            sys.exit(ExitCode.FAILURE)

        try:
            service_id = get_service_id(session, service)
            rule = session.ServiceAutoScalingRule.create(
                service_id,
                metric_source,
                metric_name,
                _threshold,
                comparator,
                step_size,
                cooldown_seconds,
                min_replicas=min_replicas,
                max_replicas=max_replicas,
            )
            print_done(f"Auto-scaling Rule (ID {rule.rule_id}) created.")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@auto_scaling_rule.command()
@pass_ctx_obj
@click.argument("service", type=str, metavar="SERVICE_NAME_OR_ID")
@click.option(
    "-f",
    "--format",
    default=None,
    help="Display only specified fields.  When specifying multiple fields separate them with comma (,).",
)
@click.option("--filter", "filter_", default=None, help="Set the query filter expression.")
@click.option("--order", default=None, help="Set the query ordering expression.")
@click.option("--offset", default=0, help="The index of the current page start for pagination.")
@click.option("--limit", type=int, default=None, help="The page size for pagination.")
def list(
    ctx: CLIContext,
    service: str,
    format: Optional[str],
    filter_: Optional[str],
    order: Optional[str],
    offset: int,
    limit: Optional[int],
) -> None:
    """List all set auto-scaling rules for given model service."""

    if format:
        try:
            fields = [service_auto_scaling_rule_fields[f.strip()] for f in format.split(",")]
        except KeyError as e:
            ctx.output.print_fail(f"Field {str(e)} not found")
            sys.exit(ExitCode.FAILURE)
    else:
        fields = None
    with Session() as session:
        service_id = get_service_id(session, service)

        try:
            fetch_func = lambda pg_offset, pg_size: session.ServiceAutoScalingRule.paginated_list(
                service_id,
                page_offset=pg_offset,
                page_size=pg_size,
                filter=filter_,
                order=order,
                fields=fields,
            )
            ctx.output.print_paginated_list(
                fetch_func,
                initial_page_offset=offset,
                page_size=limit,
            )
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@auto_scaling_rule.command()
@pass_ctx_obj
@click.argument("rule", type=click.UUID, metavar="RULE_ID")
@click.option(
    "-f",
    "--format",
    default=None,
    help="Display only specified fields.  When specifying multiple fields separate them with comma (,).",
)
def get(ctx: CLIContext, rule: UUID, format: str) -> None:
    """Prints attributes of the given auto-scaling rule."""
    fields: Iterable[Any]
    if format:
        try:
            fields = [service_auto_scaling_rule_fields[f.strip()] for f in format.split(",")]
        except KeyError as e:
            ctx.output.print_fail(f"Field {str(e)} not found")
            sys.exit(ExitCode.FAILURE)
    else:
        fields = _default_get_fields

    with Session() as session:
        try:
            rule_instance = session.ServiceAutoScalingRule(rule).get(fields=fields)
        except (ValueError, BackendAPIError):
            ctx.output.print_fail(f"Rule {rule!r} not found.")
            sys.exit(ExitCode.FAILURE)

        ctx.output.print_item(rule_instance, fields)


@auto_scaling_rule.command()
@pass_ctx_obj
@click.argument("rule", type=click.UUID, metavar="RULE_ID")
@click.option(
    "--metric-source",
    type=OptionalType(click.Choice([*AutoScalingMetricSource], case_sensitive=False)),
    default=undefined,
)
@click.option("--metric-name", type=OptionalType(str), default=undefined)
@click.option("--threshold", type=OptionalType(str), default=undefined)
@click.option(
    "--comparator",
    type=OptionalType(click.Choice([*AutoScalingMetricComparator], case_sensitive=False)),
    default=undefined,
)
@click.option("--step-size", type=OptionalType(int), default=undefined)
@click.option("--cooldown-seconds", type=OptionalType(int), default=undefined)
@click.option(
    "--min-replicas",
    type=OptionalType(int),
    help="Set as -1 to remove min_replicas restriction.",
    default=undefined,
)
@click.option(
    "--max-replicas",
    type=OptionalType(int),
    help="Set as -1 to remove max_replicas restriction.",
    default=undefined,
)
def update(
    ctx: CLIContext,
    rule: UUID,
    *,
    metric_source: str | Undefined,
    metric_name: str | Undefined,
    threshold: str | Undefined,
    comparator: str | Undefined,
    step_size: int | Undefined,
    cooldown_seconds: int | Undefined,
    min_replicas: Optional[int] | Undefined,
    max_replicas: Optional[int] | Undefined,
) -> None:
    """Update attributes of the given auto-scaling rule."""
    with Session() as session:
        try:
            _threshold = decimal.Decimal(threshold) if threshold != undefined else undefined
        except decimal.InvalidOperation:
            ctx.output.print_fail(f"{threshold} is not a valid Decimal")
            sys.exit(ExitCode.FAILURE)

        if min_replicas == -1:
            min_replicas = None
        if max_replicas == -1:
            max_replicas = None

        try:
            rule_instance = session.ServiceAutoScalingRule(rule)
            rule_instance.get()
            rule_instance.update(
                metric_source=metric_source,
                metric_name=metric_name,
                threshold=_threshold,
                comparator=comparator,
                step_size=step_size,
                cooldown_seconds=cooldown_seconds,
                min_replicas=min_replicas,
                max_replicas=max_replicas,
            )
            print_done(f"Auto-scaling Rule (ID {rule_instance.rule_id}) updated.")
        except BackendAPIError as e:
            ctx.output.print_fail(e.data["title"])
            sys.exit(ExitCode.FAILURE)


@auto_scaling_rule.command()
@pass_ctx_obj
@click.argument("rule", type=click.UUID, metavar="RULE_ID")
def delete(ctx: CLIContext, rule: UUID) -> None:
    """Remove the given auto-scaling rule."""
    with Session() as session:
        rule_instance = session.ServiceAutoScalingRule(rule)
        try:
            rule_instance.get(fields=[service_auto_scaling_rule_fields["id"]])
            rule_instance.delete()
            print_done(f"Autosscaling rule {rule_instance.rule_id} has been deleted.")
        except BackendAPIError as e:
            ctx.output.print_fail(f"Failed to delete rule {rule_instance.rule_id}:")
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)
