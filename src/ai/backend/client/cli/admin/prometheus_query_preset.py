import sys
from typing import Any
from uuid import UUID

import click

from ai.backend.cli.params import JSONParamType
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
def list(ctx: CLIContext) -> None:
    """List all prometheus query presets."""
    with Session() as session:
        try:
            items = session.PrometheusQueryPreset.list_presets()
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
    "--options",
    type=JSONParamType(),
    default=None,
    help='Preset options JSON (e.g. \'{"filter_labels":["k"],"group_labels":["k"]}\').',
)
def add(
    ctx: CLIContext,
    name: str,
    metric_name: str,
    query_template: str,
    time_window: str | None,
    options: dict[str, Any] | None,
) -> None:
    """Create a new prometheus query preset."""
    with Session() as session:
        try:
            result = session.PrometheusQueryPreset.create(
                name,
                metric_name,
                query_template,
                time_window=time_window,
                options=options,
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
    "--options",
    type=JSONParamType(),
    default=None,
    help="New preset options JSON.",
)
def modify(
    ctx: CLIContext,
    preset_id: str,
    name: str | None,
    metric_name: str | None,
    query_template: str | None,
    time_window: str | None,
    options: dict[str, Any] | None,
) -> None:
    """Modify an existing prometheus query preset."""
    with Session() as session:
        try:
            result = session.PrometheusQueryPreset.modify(
                UUID(preset_id),
                name=name,
                metric_name=metric_name,
                query_template=query_template,
                time_window=time_window,
                options=options,
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
