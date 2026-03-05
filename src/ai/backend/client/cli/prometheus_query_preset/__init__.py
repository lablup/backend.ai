"""Prometheus Query Preset CLI package."""

import click


@click.group()
def prometheus_query_preset() -> None:
    """Prometheus query preset operations."""


from . import commands  # noqa
