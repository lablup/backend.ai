"""Execute command for prometheus query presets."""

from __future__ import annotations

import json
import sys
from uuid import UUID

import click

from ai.backend.cli.types import ExitCode
from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.types import CLIContext
from ai.backend.client.session import Session

from . import prometheus_query_preset


@prometheus_query_preset.command()
@pass_ctx_obj
@click.argument("preset_id", type=str)
@click.option("--start", type=str, required=True, help="Start time (ISO8601).")
@click.option("--end", type=str, required=True, help="End time (ISO8601).")
@click.option("--step", type=str, required=True, help="Step duration (e.g. 60s).")
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
@click.option("--window", type=str, default=None, help="Time window override.")
def execute(
    ctx: CLIContext,
    preset_id: str,
    start: str,
    end: str,
    step: str,
    labels: tuple[str, ...],
    group_labels: str | None,
    window: str | None,
) -> None:
    """Execute a prometheus query preset."""
    with Session() as session:
        try:
            label_entries: list[dict[str, str]] = []
            for label in labels:
                if "=" not in label:
                    print(f"Invalid label format: {label} (expected key=value)", file=sys.stderr)
                    sys.exit(ExitCode.INVALID_ARGUMENT)
                key, value = label.split("=", 1)
                label_entries.append({"key": key, "value": value})

            group_labels_list: list[str] | None = None
            if group_labels is not None:
                group_labels_list = [gl.strip() for gl in group_labels.split(",") if gl.strip()]

            response = session.PrometheusQueryPreset.execute(
                UUID(preset_id),
                start=start,
                end=end,
                step=step,
                labels=label_entries if label_entries else None,
                group_labels=group_labels_list,
                window=window,
            )
            print(json.dumps(response.model_dump(mode="json"), indent=2, default=str))
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)
