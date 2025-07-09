"""
Configuration management CLI commands for Backend.AI Manager.

This module provides CLI commands for generating and managing configuration files.
"""

import pathlib

import click

from ai.backend.common.configs.sample_generator import generate_sample_config_file
from ai.backend.manager.config.unified import ManagerUnifiedConfig

from .context import CLIContext


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
    default="./configs/manager/sample.toml",
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
    Generate a sample configuration file from the ManagerUnifiedConfig schema.

    This command creates a TOML configuration file with all available options,
    their default values, descriptions, and examples based on the Pydantic
    model definition of ManagerUnifiedConfig.
    """
    if output.exists() and not overwrite:
        click.echo(
            f"Error: Output file '{output}' already exists. Use --overwrite to replace it.",
            err=True,
        )
        return

    header_comment = """
Backend.AI Manager Configuration Sample

This is a sample configuration file for the Backend.AI Manager.
All configuration options are documented with their descriptions,
default values, and examples.

Generated automatically from the ManagerUnifiedConfig schema.
"""

    try:
        generate_sample_config_file(
            ManagerUnifiedConfig, str(output), header_comment=header_comment.strip()
        )
        click.echo(f"Sample configuration file generated successfully: {output}")
    except Exception as e:
        click.echo(f"Error generating sample configuration: {e}", err=True)
        raise click.ClickException(f"Failed to generate sample configuration: {e}")


if __name__ == "__main__":
    cli()
