"""
Configuration management CLI commands for Backend.AI Agent.

This module provides CLI commands for generating and managing configuration files.
"""

import json
import logging
import pathlib

import click

from ai.backend.common.configs.sample_generator import generate_sample_config_file
from ai.backend.logging.utils import BraceStyleAdapter

from ..config.unified import AgentUnifiedConfig
from .context import CLIContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@click.group()
def cli() -> None:
    """Configuration management commands."""
    pass


@cli.command()
@click.option(
    "-o",
    "--output",
    type=click.Path(
        file_okay=True,
        dir_okay=False,
        writable=True,
        path_type=pathlib.Path,
    ),
    default="./configs/agent/sample.toml",
    help="Output path for the generated sample configuration file. (default: sample.toml)",
)
@click.option(
    "--overwrite",
    is_flag=True,
    help="Overwrite the output file if it already exists.",
)
@click.pass_obj
def generate_sample(
    cli_ctx: CLIContext,
    output: pathlib.Path,
    overwrite: bool,
) -> None:
    """
    Generate a sample configuration file from the AgentUnifiedConfig schema.

    This command creates a TOML configuration file with all available options,
    their default values, descriptions, and examples based on the Pydantic
    model definition of AgentUnifiedConfig.
    """
    if output.exists() and not overwrite:
        click.echo(
            f"Error: Output file '{output}' already exists. Use --overwrite to replace it.",
            err=True,
        )
        return

    header_comment = """
Backend.AI Agent Configuration Sample

This is a sample configuration file for the Backend.AI Agent.
All configuration options are documented with their descriptions,
default values, and examples.

Generated automatically from the AgentUnifiedConfig schema.
"""

    try:
        generate_sample_config_file(
            AgentUnifiedConfig, str(output), header_comment=header_comment.strip()
        )
        log.info("Sample configuration file generated successfully: {}", output)
    except Exception as e:
        raise click.ClickException(f"Failed to generate sample configuration: {e}")


@cli.command()
@click.argument(
    "path",
    metavar="PATH",
    type=click.Path(
        file_okay=True,
        dir_okay=False,
        writable=True,
        path_type=pathlib.Path,
    ),
)
@click.pass_obj
def generate_json_schema(
    cli_ctx: CLIContext,
    path: pathlib.Path,
) -> None:
    """
    Generate a JSON schema file for the Agent configuration.
    """

    try:
        raw_schema = AgentUnifiedConfig.schema_to_dict()
        with open(path, "w") as fw:
            json.dump(raw_schema, fw, indent=2)
    except Exception as e:
        raise click.ClickException(f"Failed to generate JSON schema: {e}")


if __name__ == "__main__":
    cli()


if __name__ == "__main__":
    cli()
