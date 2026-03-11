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


@admin.group()
def prometheus_query_preset() -> None:
    """Prometheus query preset administration commands."""


@prometheus_query_preset.command()
@pass_ctx_obj
@click.option("--filter-name", type=str, default=None, help="Filter by name (contains match).")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
@click.option("--limit", type=int, default=20, help="Maximum items to return.")
def search(ctx: CLIContext, filter_name: str | None, offset: int, limit: int) -> None:
    """Search prometheus query presets."""
    with Session() as session:
        try:
            data = session.PrometheusQueryPreset.search(
                filter_name=filter_name,
                offset=offset,
                limit=limit,
            )
            items = data.get("items", [])
            pagination = data.get("pagination", {})
            if not items:
                print("No presets found.")
                return
            for preset in items:
                print(f"ID: {preset['id']}")
                print(f"  Name: {preset['name']}")
                print(f"  Metric: {preset['metric_name']}")
                print(f"  Time Window: {preset.get('time_window', '-')}")
                print(f"  Created: {preset['created_at']}")
                print()
            total = pagination.get("total", "?")
            print(
                f"Total: {total} (offset={pagination.get('offset', 0)}, limit={pagination.get('limit', limit)})"
            )
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@prometheus_query_preset.command()
@pass_ctx_obj
@click.argument("preset_id", type=str)
def info(ctx: CLIContext, preset_id: str) -> None:
    """Show details of a prometheus query preset."""
    with Session() as session:
        try:
            preset = session.PrometheusQueryPreset.get(UUID(preset_id))
            print(f"ID: {preset['id']}")
            print(f"Name: {preset['name']}")
            print(f"Metric Name: {preset['metric_name']}")
            print(f"Query Template: {preset['query_template']}")
            print(f"Time Window: {preset.get('time_window', '-')}")
            options = preset.get("options", {})
            print(f"Filter Labels: {options.get('filter_labels', [])}")
            print(f"Group Labels: {options.get('group_labels', [])}")
            print(f"Created: {preset['created_at']}")
            print(f"Updated: {preset['updated_at']}")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@prometheus_query_preset.command()
@pass_ctx_obj
@click.option("--name", type=str, required=True, help="Preset name.")
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
    """Create a new prometheus query preset."""
    with Session() as session:
        try:
            fl = [s.strip() for s in filter_labels.split(",") if s.strip()] if filter_labels else []
            gl = [s.strip() for s in group_labels.split(",") if s.strip()] if group_labels else []
            result = session.PrometheusQueryPreset.create(
                name,
                metric_name,
                query_template,
                time_window=time_window,
                filter_labels=fl,
                group_labels=gl,
            )
            print(f"Created preset: {result['id']}")
            print_done("Done.")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@prometheus_query_preset.command()
@pass_ctx_obj
@click.argument("preset_id", type=str)
@click.option("--name", type=str, default=None, help="New preset name.")
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
    preset_id: str,
    name: str | None,
    metric_name: str | None,
    query_template: str | None,
    time_window: str | None,
    filter_labels: str | None,
    group_labels: str | None,
) -> None:
    """Modify an existing prometheus query preset."""
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
            result = session.PrometheusQueryPreset.modify(
                UUID(preset_id),
                name=name,
                metric_name=metric_name,
                query_template=query_template,
                time_window=time_window,
                filter_labels=fl,
                group_labels=gl,
            )
            print(f"Modified preset: {result['id']}")
            print_done("Done.")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@prometheus_query_preset.command()
@pass_ctx_obj
@click.argument("preset_id", type=str)
@click.confirmation_option(prompt="Are you sure you want to delete this preset?")
def delete(ctx: CLIContext, preset_id: str) -> None:
    """Delete a prometheus query preset."""
    with Session() as session:
        try:
            _result = session.PrometheusQueryPreset.delete(UUID(preset_id))
            print(f"Deleted preset: {preset_id}")
            print_done("Done.")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@prometheus_query_preset.command()
@pass_ctx_obj
@click.argument("preset_id", type=str)
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
    preset_id: str,
    start: str | None,
    end: str | None,
    step: str | None,
    labels: tuple[str, ...],
    group_labels: str | None,
    time_window: str | None,
) -> None:
    """Execute a prometheus query preset."""
    with Session() as session:
        try:
            filter_labels: list[dict[str, str]] | None = None
            if labels:
                filter_labels = []
                for label in labels:
                    if "=" not in label:
                        print(
                            f"Invalid label format: {label} (expected key=value)", file=sys.stderr
                        )
                        sys.exit(ExitCode.INVALID_ARGUMENT)
                    key, value = label.split("=", 1)
                    filter_labels.append({"key": key, "value": value})

            group_labels_list: list[str] | None = None
            if group_labels is not None:
                group_labels_list = [gl.strip() for gl in group_labels.split(",") if gl.strip()]

            time_range: dict[str, str] | None = None
            if start is not None and end is not None and step is not None:
                time_range = {"start": start, "end": end, "step": step}

            response = session.PrometheusQueryPreset.execute(
                UUID(preset_id),
                filter_labels=filter_labels,
                group_labels=group_labels_list,
                time_window=time_window,
                time_range=time_range,
            )
            print(json.dumps(response, indent=2, default=str))
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)
