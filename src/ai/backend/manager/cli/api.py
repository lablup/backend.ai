from __future__ import annotations

import asyncio
import importlib
import json
import logging
import textwrap
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING, Any

import aiofiles
import aiohttp_cors
import click
import graphene

from ai.backend.manager import __version__
from ai.backend.manager.openapi import get_path_parameters, parse_traferet_definition
from ai.backend.manager.server import global_subapp_pkgs

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


async def generate_openapi(output_path: Path) -> None:
    cors_options = {
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=False, expose_headers="*", allow_headers="*"
        ),
    }

    openapi: dict[str, Any] = {
        "openapi": "3.0.0",
        "info": {
            "title": "Backend.AI Manager API",
            "description": "Backend.AI Manager REST API specification",
            "version": __version__,
        },
        "components": {
            "securitySchemes": {
                "TokenAuth": {"type": "ApiKey", "in": "header", "name": "Authorization: BackendAI"},
            }
        },
        "paths": defaultdict(lambda: {}),
    }
    operation_id_mapping: defaultdict[str, int] = defaultdict(lambda: 0)
    for subapp in global_subapp_pkgs:
        pkg = importlib.import_module("ai.backend.manager.api" + subapp)
        app, _ = pkg.create_app(cors_options)
        prefix = app.get("prefix", "root")
        for route in app.router.routes():
            resource = route.resource
            if not resource:
                continue

            path = "/" + ("" if prefix == "root" else prefix) + resource.canonical
            method = route.method

            if method == "OPTIONS":
                continue

            operation_id = f"{prefix}.{route.handler.__name__}"
            print(f"parsing {operation_id}")
            operation_id_mapping[operation_id] += 1
            if (operation_id_count := operation_id_mapping[operation_id]) > 1:
                operation_id += f".{operation_id_count}"

            description = []
            if route.handler.__doc__:
                description.append(textwrap.dedent(route.handler.__doc__))

            route_def = {
                "operationId": operation_id,
                "tags": [prefix],
                "responses": {"200": {"description": "Successful response"}},
            }
            parameters = []
            parameters.extend(get_path_parameters(resource))
            if hasattr(route.handler, "_backend_attrs"):
                preconds = []
                handler_attrs = getattr(route.handler, "_backend_attrs")
                if handler_attrs.get("auth_required"):
                    route_def["security"] = [{"TokenAuth": []}]
                if auth_scope := handler_attrs.get("auth_scope"):
                    preconds.append(f"{auth_scope.capitalize()} privilege required.")
                if manager_status := handler_attrs.get("required_server_statuses"):
                    if len(manager_status) > 0:
                        preconds.append(
                            f"Manager status required: {list(manager_status)[0].value.upper()}"
                        )
                    else:
                        preconds.append(
                            "Manager status required: one of "
                            f"{', '.join([e.value.upper() for e in manager_status])}"
                        )
                if preconds:
                    description.append("\n**Preconditions:**")
                    for item in preconds:
                        description.append(f"* {item}")
                    description.append("")
                if request_scheme := handler_attrs.get("request_scheme"):
                    parsed_definition = parse_traferet_definition(request_scheme)
                    if method == "GET" or method == "DELETE":
                        parameters.extend([{**d, "in": "query"} for d in parsed_definition])
                    else:
                        properties = {d["name"]: d["schema"] for d in parsed_definition}
                        required_keys: list[str] = [
                            d["name"] for d in parsed_definition if d["required"]
                        ]
                        route_def["requestBody"] = {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": properties,
                                        "required": required_keys,
                                    }
                                }
                            }
                        }
            route_def["parameters"] = parameters
            route_def["description"] = "\n".join(description)
            openapi["paths"][path][method.lower()] = route_def
    if output_path == "-" or output_path is None:
        print(json.dumps(openapi, ensure_ascii=False, indent=2))
    else:
        async with aiofiles.open(output_path, mode="w") as fw:
            await fw.write(json.dumps(openapi, ensure_ascii=False, indent=2))


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
    asyncio.run(generate_openapi(output))
