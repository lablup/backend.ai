from __future__ import annotations

import asyncio
import importlib
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import aiofiles
import aiohttp_cors
import click
import graphene
from aiohttp import web

from ai.backend.manager.openapi import generate_openapi

from ..models.gql import Mutations, Queries

if TYPE_CHECKING:
    from .context import CLIContext

log = logging.getLogger(__spec__.name)


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


async def _generate() -> dict[str, Any]:
    from ai.backend.manager.server import global_subapp_pkgs

    cors_options = {
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=False, expose_headers="*", allow_headers="*"
        ),
    }

    subapps: list[web.Application] = []
    for subapp in global_subapp_pkgs:
        pkg = importlib.import_module("ai.backend.manager.api" + subapp)
        app, _ = pkg.create_app(cors_options)
        subapps.append(app)
    return generate_openapi(subapps, verbose=True)


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
    openapi = asyncio.run(_generate())
    if output == "-" or output is None:
        print(json.dumps(openapi, ensure_ascii=False, indent=2))
    else:
        with open(output, mode="w") as fw:
            fw.write(json.dumps(openapi, ensure_ascii=False, indent=2))
