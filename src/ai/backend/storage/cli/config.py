"""
Configuration management CLI commands for Backend.AI Storage Proxy.

This module provides CLI commands for generating and managing configuration files.
"""

import logging
import pathlib

import click

from ai.backend.common.configs.sample_generator import generate_sample_config_file
from ai.backend.logging.utils import BraceStyleAdapter

from ..config.unified import StorageProxyUnifiedConfig
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
    default="./configs/storage-proxy/sample.toml",
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
    Generate a sample configuration file from the StorageProxyUnifiedConfig schema.

    This command creates a TOML configuration file with all available options,
    their default values, descriptions, and examples based on the Pydantic
    model definition of StorageProxyUnifiedConfig.
    """
    if output.exists() and not overwrite:
        click.echo(
            f"Error: Output file '{output}' already exists. Use --overwrite to replace it.",
            err=True,
        )
        return

    header_comment = """
Backend.AI Storage Proxy Configuration Sample

This is a sample configuration file for the Backend.AI Storage Proxy.
All configuration options are documented with their descriptions,
default values, and examples.

Generated automatically from the StorageProxyUnifiedConfig schema.
"""

    try:
        generate_sample_config_file(
            StorageProxyUnifiedConfig, str(output), header_comment=header_comment.strip()
        )
        log.info(f"Sample configuration file generated successfully: {output}")
    except Exception as e:
        raise click.ClickException(f"Failed to generate sample configuration: {e}")


if __name__ == "__main__":
    cli()
