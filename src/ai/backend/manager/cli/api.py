from __future__ import annotations

import asyncio
import logging
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import aiofiles
import click
import graphene_federation

from ai.backend.common.json import pretty_json_str
from ai.backend.manager.openapi import generate

from ..api.gql.schema import schema as strawberry_schema
from ..models.gql import Mutations, Queries

if TYPE_CHECKING:
    from .context import CLIContext

log = logging.getLogger(__spec__.name)


@click.group()
def cli(args) -> None:
    pass


async def generate_graphene_gql_schema(output_path: Path) -> None:
    schema = graphene_federation.build_schema(
        query=Queries,
        mutation=Mutations,
        auto_camelcase=False,
        federation_version=graphene_federation.LATEST_VERSION,
    )
    if output_path == "-":
        log.info("======== Graphene GraphQL API Schema ========")
        print(str(schema))
    else:
        async with aiofiles.open(output_path, "w") as fw:
            await fw.write(str(schema))


async def generate_strawberry_gql_schema(output_path: Path) -> None:
    if output_path == "-":
        log.info("======== Strawberry GraphQL API Schema ========")
        print(strawberry_schema.as_str())
    else:
        async with aiofiles.open(output_path, "w") as fw:
            await fw.write(strawberry_schema.as_str())


def generate_supergraph_schema(
    schema_file_path: str | Path,
    supergraph_config_path: str | Path,
    output_dir: Optional[str | Path] = None,
) -> None:
    """
    Post-processes GraphQL schema and generates supergraph.

    Args:
        schema_file_path: Path to the main schema file (e.g., schema2.graphql)
        supergraph_config_path: Path to the supergraph.yaml configuration file
        output_dir: Output directory (defaults to same directory as schema file)
    """
    log.info("Generating supergraph schema...")

    schema_path = Path(schema_file_path)
    config_path = Path(supergraph_config_path)
    output_dir = Path(output_dir) if output_dir else schema_path.parent

    # Post-process schema file
    content = schema_path.read_text(encoding="utf-8")
    original_content = content
    content = content.replace("type PageInfo {", "type PageInfo @shareable {").replace(
        'import: ["@external", "@key"]', 'import: ["@external", "@key", "@shareable"]'
    )
    schema_path.write_text(content, encoding="utf-8")
    print(f"Schema post-processed at: {schema_path}")

    try:
        # Generate supergraph
        supergraph_path = output_dir / "supergraph.graphql"
        # Find the project root directory (where the supergraph.yaml paths are relative to)
        project_root = config_path
        while project_root.parent != project_root:
            if (project_root / "pyproject.toml").exists() or (project_root / ".git").exists():
                break
            project_root = project_root.parent

        result = subprocess.run(
            ["rover", "supergraph", "compose", "--config", str(config_path)],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )

        supergraph_path.write_text(result.stdout, encoding="utf-8")
        print(f"Supergraph generated at: {supergraph_path}")
    except subprocess.CalledProcessError:
        # Restore original schema file on error
        schema_path.write_text(original_content, encoding="utf-8")
        raise


@cli.command()
@click.pass_obj
@click.option(
    "--schema-file",
    "-s",
    required=True,
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help="Path to the GraphQL schema file to process",
)
@click.option(
    "--config",
    "-c",
    required=True,
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help="Path to the supergraph.yaml configuration file",
)
@click.option(
    "--output-dir",
    "-o",
    default=None,
    type=click.Path(file_okay=False, writable=True),
    help="Output directory for supergraph.graphql (default: same as schema file directory)",
)
def generate_supergraph(
    cli_ctx: CLIContext, schema_file: Path, config: Path, output_dir: Optional[Path]
) -> None:
    """Post-process GraphQL schema and generate supergraph."""
    try:
        generate_supergraph_schema(
            schema_file_path=schema_file,
            supergraph_config_path=config,
            output_dir=output_dir,
        )
        click.echo("✅ Supergraph generation completed successfully!")
    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ Rover command failed: {e}", err=True)
        if hasattr(e, "stderr") and e.stderr:
            click.echo(f"Error details: {e.stderr}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.pass_obj
@click.option(
    "--output",
    "-o",
    default="-",
    type=click.Path(dir_okay=False, writable=True),
    help="Output file path (default: stdout)",
)
@click.option(
    "--v2",
    is_flag=True,
    default=False,  # TODO: Set default to True after v2 migration is complete
    help="Generate strawberry based v2 GraphQL schema (default: False)",
)
def dump_gql_schema(cli_ctx: CLIContext, output: Path, v2: bool) -> None:
    if v2:
        asyncio.run(generate_strawberry_gql_schema(output))
    else:
        asyncio.run(generate_graphene_gql_schema(output))


@cli.command()
@click.pass_obj
@click.option(
    "--output",
    "-o",
    default="-",
    type=click.Path(dir_okay=False, writable=True),
    help="Output file path (default: stdout)",
)
def dump_openapi(cli_ctx: CLIContext, output: Path) -> None:
    """
    Generates OpenAPI specification of Backend.AI API.
    """
    openapi = asyncio.run(generate())
    if output == "-" or output is None:
        print(pretty_json_str(openapi))
    else:
        with open(output, mode="w") as fw:
            fw.write(pretty_json_str(openapi))
