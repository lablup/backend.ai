"""
Configuration management CLI commands for Backend.AI Storage Proxy.

This module provides CLI commands for generating and managing configuration files.
"""

import pathlib

import click
import tomli

from ai.backend.common.configs.sample_generator import generate_sample_config_file
from ai.backend.storage.config.unified import StorageProxyUnifiedConfig


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
def generate_sample(
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
        click.echo(f"Sample configuration file generated successfully: {output}")
    except Exception as e:
        click.echo(f"Error generating sample configuration: {e}", err=True)
        raise click.ClickException(f"Failed to generate sample configuration: {e}")


@cli.command()
@click.option(
    "-p",
    "--path",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        path_type=pathlib.Path,
    ),
    default="./configs/storage-proxy/halfstack.yaml",
    help="Path to the configuration file to validate. (default: ./configs/storage-proxy/halfstack.yaml)",
)
def validate(
    path: pathlib.Path,
) -> None:
    """
    Validate a configuration file using the StorageProxyUnifiedConfig schema.
    
    This command loads and validates a TOML configuration file against
    the StorageProxyUnifiedConfig Pydantic model to ensure it's valid.
    """
    try:
        with open(path, "rb") as f:
            config_data = tomli.load(f)
        
        config = StorageProxyUnifiedConfig.model_validate(config_data)
        config.model_dump()
        
        click.echo(f"Configuration file '{path}' is valid.")
    except FileNotFoundError:
        click.echo(f"Error: Configuration file '{path}' not found.", err=True)
        raise click.ClickException(f"Configuration file not found: {path}")
    except tomli.TOMLDecodeError as e:
        click.echo(f"Error: Invalid TOML format in '{path}': {e}", err=True)
        raise click.ClickException(f"Invalid TOML format: {e}")
    except Exception as e:
        click.echo(f"Error: Configuration validation failed for '{path}': {e}", err=True)
        raise click.ClickException(f"Configuration validation failed: {e}")


if __name__ == "__main__":
    cli()