"""
Configuration management CLI commands for Backend.AI Agent.

This module provides CLI commands for generating and managing configuration files.
"""

import logging
import pathlib

import click

from ai.backend.agent.config.unified import AgentUnifiedConfig
from ai.backend.common.cli import LazyGroup
from ai.backend.common.configs.generator import (
    GeneratorConfig,
    TOMLGenerator,
)
from ai.backend.common.meta import ConfigEnvironment
from ai.backend.logging.utils import BraceStyleAdapter

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
    "-e",
    "--env",
    type=click.Choice(["local", "prod"]),
    default="prod",
    help="Target environment for example values. (default: prod)",
)
@click.option(
    "--overwrite",
    is_flag=True,
    help="Overwrite the output file if it already exists.",
)
@click.option(
    "--unmask-secrets",
    is_flag=True,
    help="Show actual secret values instead of masking them.",
)
@click.pass_obj
def generate_sample(
    _cli_ctx: CLIContext,
    output: pathlib.Path,
    env: str,
    overwrite: bool,
    unmask_secrets: bool,
) -> None:
    """
    Generate a sample configuration file from the AgentUnifiedConfig schema.

    This command creates a TOML configuration file with environment-specific examples
    (local or prod), proper secret masking, and comprehensive documentation from
    BackendAIConfigMeta annotations.

    Features:
    - Environment-specific examples (--env local|prod)
    - Secret field masking (use --unmask-secrets to show actual values)
    - Comprehensive field documentation from BackendAIConfigMeta
    """
    if output.exists() and not overwrite:
        click.echo(
            f"Error: Output file '{output}' already exists. Use --overwrite to replace it.",
            err=True,
        )
        return

    header_comment = f"""
Backend.AI Agent Configuration ({env.upper()} Environment)

This is a sample configuration file for the Backend.AI Agent.
All configuration options are documented with their descriptions,
default values, and environment-specific examples.

Generated using BackendAIConfigMeta annotations.
"""

    config_env = ConfigEnvironment.LOCAL if env == "local" else ConfigEnvironment.PROD

    try:
        generator_config = GeneratorConfig(
            mask_secrets=not unmask_secrets,
            include_version_comments=True,
        )
        generator = TOMLGenerator(env=config_env, config=generator_config)
        generator.generate_to_file(AgentUnifiedConfig, output, header=header_comment.strip())
        log.info("Sample configuration file generated successfully: {}", output)
    except Exception as e:
        raise click.ClickException(f"Failed to generate sample configuration: {e}") from e


@cli.group(cls=LazyGroup, import_name="ai.backend.agent.cli.config_migrate:cli")
def migrate() -> None:
    """Migrate legacy configuration fields."""


if __name__ == "__main__":
    cli()
