from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING

import aiofiles
import click
import graphene

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
    schema = graphene.Schema(query=Queries, mutation=Mutations, auto_camelcase=False)
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
