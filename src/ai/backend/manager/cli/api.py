from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING

import aiofiles
import click
import graphene

from ..models.gql import Mutations, Queries

if TYPE_CHECKING:
    from .context import CLIContext

log = logging.getLogger(__spec__.name)  # type: ignore[name-defined]


@click.group()
def cli(args) -> None:
    pass


async def generate_gql_schema(output_path: Path) -> None:
    schema = graphene.Schema(query=Queries, mutation=Mutations, auto_camelcase=False)
    if output_path == "-":
        log.info("======== GraphQL API Schema ========")
        print(str(schema))
    else:
        async with aiofiles.open(output_path, "w") as fw:
            await fw.write(str(schema))


@cli.command()
@click.pass_obj
@click.option(
    "--output",
    "-o",
    default="-",
    type=click.Path(dir_okay=False, writable=True),
    help="Output file path (default: stdout)",
)
def dump_gql_schema(cli_ctx: CLIContext, output: Path) -> None:
    asyncio.run(generate_gql_schema(output))
