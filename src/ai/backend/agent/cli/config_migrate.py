"""
Configuration migration CLI commands for Backend.AI Agent.
"""

import pathlib

import click

from ai.backend.agent.config.sd_migration import AGENT_MAPPING_RULES
from ai.backend.common.configs.migration.cli import run_sd_migration, sd_migration_options


@click.group()
def cli() -> None:
    """Migrate legacy configuration fields."""
    pass


@cli.command(name="service-discovery")
@sd_migration_options
def service_discovery(
    input_path: pathlib.Path,
    output_path: pathlib.Path | None,
    append: bool,
    dry_run: bool,
    force: bool,
) -> None:
    """Migrate address/port fields to [service-discovery.endpoints]."""
    run_sd_migration(
        input_path=input_path,
        output_path=output_path,
        append=append,
        dry_run=dry_run,
        force=force,
        component_name="agent",
        mapping_rules=AGENT_MAPPING_RULES,
    )
