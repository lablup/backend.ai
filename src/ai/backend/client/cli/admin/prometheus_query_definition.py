import json
import sys
from uuid import UUID

import click

from ai.backend.cli.types import ExitCode
from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.pretty import print_done
from ai.backend.client.cli.types import CLIContext
from ai.backend.client.session import Session

from . import admin


def _parse_label_filters(labels: tuple[str, ...]) -> list[dict[str, str]] | None:
    if not labels:
        return None
    parsed: list[dict[str, str]] = []
    for label in labels:
        if "=" not in label:
            print(f"Invalid label format: {label} (expected key=value)", file=sys.stderr)
            sys.exit(ExitCode.INVALID_ARGUMENT)
        key, value = label.split("=", 1)
        parsed.append({"key": key, "value": value})
    return parsed


@admin.group()
def prometheus_query_definition() -> None:
    """Prometheus query definition administration commands."""


@prometheus_query_definition.command()
@pass_ctx_obj
@click.option("--filter-name", type=str, default=None, help="Filter by name (contains match).")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
@click.option("--limit", type=int, default=20, help="Maximum items to return.")
def search(ctx: CLIContext, filter_name: str | None, offset: int, limit: int) -> None:
    """Search prometheus query definitions."""
    with Session() as session:
        try:
            data = session.PrometheusQueryDefinition.search(
                filter_name=filter_name,
                offset=offset,
                limit=limit,
            )
            items = data.get("items", [])
            pagination = data.get("pagination", {})
            if not items:
                print("No definitions found.")
                return
            for definition in items:
                print(f"ID: {definition['id']}")
                print(f"  Name: {definition['name']}")
                print(f"  Metric: {definition['metric_name']}")
                print(f"  Time Window: {definition.get('time_window', '-')}")
                print(f"  Created: {definition['created_at']}")
                print()
            total = pagination.get("total", "?")
            print(
                f"Total: {total} (offset={pagination.get('offset', 0)}, limit={pagination.get('limit', limit)})"
            )
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@prometheus_query_definition.command()
@pass_ctx_obj
@click.argument("definition_id", type=str)
def info(ctx: CLIContext, definition_id: str) -> None:
    """Show details of a prometheus query definition."""
    with Session() as session:
        try:
            definition = session.PrometheusQueryDefinition.get(UUID(definition_id))
            print(f"ID: {definition['id']}")
            print(f"Name: {definition['name']}")
            print(f"Metric Name: {definition['metric_name']}")
            print(f"Query Template: {definition['query_template']}")
            print(f"Time Window: {definition.get('time_window', '-')}")
            options = definition.get("options", {})
            print(f"Filter Labels: {options.get('filter_labels', [])}")
            print(f"Group Labels: {options.get('group_labels', [])}")
            print(f"Created: {definition['created_at']}")
            print(f"Updated: {definition['updated_at']}")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@prometheus_query_definition.command()
@pass_ctx_obj
@click.option("--name", type=str, required=True, help="Definition name.")
@click.option("--metric-name", type=str, required=True, help="Prometheus metric name.")
@click.option("--query-template", type=str, required=True, help="PromQL template.")
@click.option("--time-window", type=str, default=None, help="Default time window (e.g. 5m).")
@click.option(
    "--filter-labels",
    type=str,
    default="",
    help="Comma-separated allowed filter label keys.",
)
@click.option(
    "--group-labels",
    type=str,
    default="",
    help="Comma-separated allowed group-by label keys.",
)
def add(
    ctx: CLIContext,
    name: str,
    metric_name: str,
    query_template: str,
    time_window: str | None,
    filter_labels: str,
    group_labels: str,
) -> None:
    """Create a new prometheus query definition."""
    with Session() as session:
        try:
            fl = [s.strip() for s in filter_labels.split(",") if s.strip()] if filter_labels else []
            gl = [s.strip() for s in group_labels.split(",") if s.strip()] if group_labels else []
            result = session.PrometheusQueryDefinition.create(
                name,
                metric_name,
                query_template,
                time_window=time_window,
                filter_labels=fl,
                group_labels=gl,
            )
            print(f"Created definition: {result['id']}")
            print_done("Done.")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@prometheus_query_definition.command()
@pass_ctx_obj
@click.argument("definition_id", type=str)
@click.option("--name", type=str, default=None, help="New definition name.")
@click.option("--metric-name", type=str, default=None, help="New Prometheus metric name.")
@click.option("--query-template", type=str, default=None, help="New PromQL template.")
@click.option("--time-window", type=str, default=None, help="New default time window.")
@click.option(
    "--filter-labels",
    type=str,
    default=None,
    help="Comma-separated allowed filter label keys.",
)
@click.option(
    "--group-labels",
    type=str,
    default=None,
    help="Comma-separated allowed group-by label keys.",
)
def modify(
    ctx: CLIContext,
    definition_id: str,
    name: str | None,
    metric_name: str | None,
    query_template: str | None,
    time_window: str | None,
    filter_labels: str | None,
    group_labels: str | None,
) -> None:
    """Modify an existing prometheus query definition."""
    with Session() as session:
        try:
            fl = (
                [s.strip() for s in filter_labels.split(",") if s.strip()]
                if filter_labels is not None
                else None
            )
            gl = (
                [s.strip() for s in group_labels.split(",") if s.strip()]
                if group_labels is not None
                else None
            )
            result = session.PrometheusQueryDefinition.modify(
                UUID(definition_id),
                name=name,
                metric_name=metric_name,
                query_template=query_template,
                time_window=time_window,
                filter_labels=fl,
                group_labels=gl,
            )
            print(f"Modified definition: {result['id']}")
            print_done("Done.")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@prometheus_query_definition.command()
@pass_ctx_obj
@click.argument("definition_id", type=str)
@click.confirmation_option(prompt="Are you sure you want to delete this definition?")
def delete(ctx: CLIContext, definition_id: str) -> None:
    """Delete a prometheus query definition."""
    with Session() as session:
        try:
            _result = session.PrometheusQueryDefinition.delete(UUID(definition_id))
            print(f"Deleted definition: {definition_id}")
            print_done("Done.")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@prometheus_query_definition.command()
@pass_ctx_obj
@click.argument("definition_id", type=str)
@click.option("--start", type=str, default=None, help="Start time (ISO8601).")
@click.option("--end", type=str, default=None, help="End time (ISO8601).")
@click.option("--step", type=str, default=None, help="Step duration (e.g. 60s).")
@click.option(
    "--label",
    "labels",
    multiple=True,
    type=str,
    help="Label filter in key=value format (repeatable).",
)
@click.option(
    "--group-labels",
    type=str,
    default=None,
    help="Comma-separated group labels.",
)
@click.option("--time-window", type=str, default=None, help="Time window override.")
def execute(
    ctx: CLIContext,
    definition_id: str,
    start: str | None,
    end: str | None,
    step: str | None,
    labels: tuple[str, ...],
    group_labels: str | None,
    time_window: str | None,
) -> None:
    """Execute a prometheus query definition."""
    with Session() as session:
        try:
            filter_labels = _parse_label_filters(labels)

            group_labels_list: list[str] | None = None
            if group_labels is not None:
                group_labels_list = [gl.strip() for gl in group_labels.split(",") if gl.strip()]

            time_range: dict[str, str] | None = None
            if start is not None and end is not None and step is not None:
                time_range = {"start": start, "end": end, "step": step}

            response = session.PrometheusQueryDefinition.execute(
                UUID(definition_id),
                filter_labels=filter_labels,
                group_labels=group_labels_list,
                time_window=time_window,
                time_range=time_range,
            )
            print(json.dumps(response, indent=2, default=str))
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)
