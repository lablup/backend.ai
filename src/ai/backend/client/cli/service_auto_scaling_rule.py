import decimal
import sys
import uuid
from typing import Any, Iterable, Optional

import click

from ai.backend.cli.types import ExitCode
from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.service import get_service_id
from ai.backend.client.cli.types import CLIContext
from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.session import Session
from ai.backend.common.types import AutoScalingMetricComparator, AutoScalingMetricSource

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
def auto_scaling_rule():
    """Set of model service auto scaling rule operations"""


@auto_scaling_rule.command()
@pass_ctx_obj
@click.argument("service", type=str, metavar="SERVICE_NAME_OR_ID")
@click.option("--metric-source", type=click.Choice([*AutoScalingMetricSource]), required=True)
@click.option("--metric-name", type=str, required=True)
@click.option("--threshold", type=str, required=True)
@click.option("--comparator", type=click.Choice([*AutoScalingMetricComparator]), required=True)
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
    """Create a new auto scaling rule."""

    with Session() as session:
        try:
            _threshold = decimal.Decimal(threshold)
        except decimal.InvalidOperation:
            ctx.output.print_fail(f"{threshold} is not a valid Decimal")
            sys.exit(ExitCode.FAILURE)

        try:
            service_id = uuid.UUID(get_service_id(session, service))
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
            print_done(f"Auto Scaling Rule (ID {rule.rule_id}) created.")
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
def list(ctx: CLIContext, service: str, format, filter_, order, offset, limit):
    """List all set auto scaling rules for given model service."""

    if format:
        try:
            fields = [service_auto_scaling_rule_fields[f.strip()] for f in format.split(",")]
        except KeyError as e:
            ctx.output.print_fail(f"Field {str(e)} not found")
            sys.exit(ExitCode.FAILURE)
    else:
        fields = None
    with Session() as session:
        service_id = uuid.UUID(get_service_id(session, service))

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
@click.argument("rule", type=str, metavar="RULE_ID")
@click.option(
    "-f",
    "--format",
    default=None,
    help="Display only specified fields.  When specifying multiple fields separate them with comma (,).",
)
def get(ctx: CLIContext, rule, format):
    fields: Iterable[Any]
    if format:
        try:
            fields = [service_auto_scaling_rule_fields[f.strip()] for f in format.split(",")]
        except KeyError as e:
            ctx.output.print_fail(f"Field {str(e)} not found")
            sys.exit(ExitCode.FAILURE)
    else:
        fields = _default_list_fields

    with Session() as session:
        try:
            rule_info = session.ServiceAutoScalingRule(uuid.UUID(rule)).get(fields=fields)
        except (ValueError, BackendAPIError):
            rules = session.Network.paginated_list(filter=f'name == "{rule}"', fields=fields)
            if rules.total_count == 0:
                ctx.output.print_fail(f"Network {rule} not found.")
                sys.exit(ExitCode.FAILURE)
            rule_info = rules.items[0]

        ctx.output.print_item(rule_info, fields)


@auto_scaling_rule.command()
@pass_ctx_obj
@click.argument("rule", type=str, metavar="NETWORK_ID_OR_NAME")
def delete(ctx: CLIContext, rule):
    with Session() as session:
        rule = session.ServiceAutoScalingRule(uuid.UUID(rule))
        try:
            rule.get(fields=[service_auto_scaling_rule_fields["id"]])
            rule.delete()
            print_done(f"Network {rule} has been deleted.")
        except BackendAPIError as e:
            ctx.output.print_fail(f"Failed to delete rule {rule}:")
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)
