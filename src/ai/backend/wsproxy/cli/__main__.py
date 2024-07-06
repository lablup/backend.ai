import asyncio
import importlib
import json
from pathlib import Path
from typing import Any

import aiohttp_cors
import click
import tomlkit
from aiohttp import web
from setproctitle import setproctitle

from ai.backend.common.types import LogSeverity

from ..config import ServerConfig, generate_example_json
from ..openapi import generate_openapi
from ..utils import ensure_json_serializable


@click.group(invoke_without_command=False, context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--log-level",
    type=click.Choice([*LogSeverity.__members__.keys()], case_sensitive=False),
    default="INFO",
    help="Set the logging verbosity level",
)
@click.pass_context
def main(
    ctx: click.Context,
    log_level: str,
) -> None:
    """
    Backend.AI WSProxy CLI
    """
    setproctitle("backend.ai: wsproxy.cli")


@main.command()
@click.option(
    "--output",
    "-o",
    default="-",
    type=click.Path(dir_okay=False, writable=True),
    help="Output file path (default: stdout)",
)
def generate_example_configuration(output: Path) -> None:
    """
    Generates example TOML configuration file for Backend.AI Proxy Coordinator.
    """
    generated_example = generate_example_json(ServerConfig)
    if output == "-" or output is None:
        print(tomlkit.dumps(ensure_json_serializable(generated_example)))
    else:
        with open(output, mode="w") as fw:
            fw.write(tomlkit.dumps(ensure_json_serializable(generated_example)))


async def _generate() -> dict[str, Any]:
    from ..server import global_subapp_pkgs

    cors_options = {
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=False, expose_headers="*", allow_headers="*"
        ),
    }

    subapps: list[web.Application] = []
    for subapp in global_subapp_pkgs:
        pkg = importlib.import_module("ai.backend.wsproxy.api" + subapp)
        app, _ = pkg.create_app(cors_options)
        subapps.append(app)
    return generate_openapi("Proxy Coordinator", subapps, verbose=True)


@main.command()
@click.option(
    "--output",
    "-o",
    default="-",
    type=click.Path(dir_okay=False, writable=True),
    help="Output file path (default: stdout)",
)
def generate_openapi_spec(output: Path) -> None:
    """
    Generates OpenAPI specification of Backend.AI API.
    """
    openapi = asyncio.run(_generate())
    if output == "-" or output is None:
        print(json.dumps(openapi, ensure_ascii=False, indent=2))
    else:
        with open(output, mode="w") as fw:
            fw.write(json.dumps(openapi, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
