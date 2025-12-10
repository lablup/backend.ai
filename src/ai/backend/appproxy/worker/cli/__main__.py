from pathlib import Path
from typing import Any, Optional

import click

from ai.backend.common.cli import LazyGroup

from .context import CLIContext

# LogLevel values for click.Choice - avoid importing ai.backend.logging at module level
_LOG_LEVELS = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "TRACE", "NOTSET"]


@click.group(invoke_without_command=False, context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "-f",
    "--config-path",
    "--config",
    type=click.Path(
        file_okay=True,
        dir_okay=False,
        exists=True,
        path_type=Path,
    ),
    default=None,
    help="The config file path. (default: ./app-proxy-worker.toml)",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Set the logging level to DEBUG",
)
@click.option(
    "--log-level",
    type=click.Choice(_LOG_LEVELS, case_sensitive=False),
    default="INFO",
    help="Set the logging verbosity level",
)
@click.pass_context
def main(
    ctx: click.Context,
    debug: bool,
    log_level: str,
    config_path: Optional[Path] = None,
) -> None:
    """
    Proxy Worker Administration CLI
    """
    from setproctitle import setproctitle

    from ai.backend.logging.types import LogLevel

    setproctitle("backend.ai: proxy-worker.cli")
    if debug:
        log_level = "DEBUG"
    ctx.obj = ctx.with_resource(CLIContext(config_path=config_path, log_level=LogLevel(log_level)))


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
    Generates example TOML configuration file for Backend.AI Proxy Worker.
    """
    import tomli_w

    from ai.backend.appproxy.common.config import generate_example_json
    from ai.backend.appproxy.common.utils import ensure_json_serializable

    from ..config import ServerConfig

    generated_example = generate_example_json(ServerConfig)
    if output == "-" or output is None:
        print(tomli_w.dumps(ensure_json_serializable(generated_example)))
    else:
        with open(output, mode="w") as fw:
            fw.write(tomli_w.dumps(ensure_json_serializable(generated_example)))


async def _generate() -> dict[str, Any]:
    import importlib

    import aiohttp_cors
    from aiohttp import web

    from ai.backend.appproxy.common.openapi import generate_openapi

    from ..server import global_subapp_pkgs

    cors_options = {
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=False, expose_headers="*", allow_headers="*"
        ),
    }

    subapps: list[web.Application] = []
    for subapp in global_subapp_pkgs:
        pkg = importlib.import_module("ai.backend.appproxy.worker.api" + subapp)
        app, _ = pkg.create_app(cors_options)
        subapps.append(app)
    return generate_openapi("Proxy Worker", subapps, verbose=True)


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
    import asyncio
    import json

    openapi = asyncio.run(_generate())
    if output == "-" or output is None:
        print(json.dumps(openapi, ensure_ascii=False, indent=2))
    else:
        with open(output, mode="w") as fw:
            fw.write(json.dumps(openapi, ensure_ascii=False, indent=2))


@main.group(cls=LazyGroup, import_name="ai.backend.appproxy.worker.cli.dependencies:cli")
def dependencies():
    """Command set for dependency verification and validation."""


@main.group(cls=LazyGroup, import_name="ai.backend.appproxy.worker.cli.health:cli")
def health():
    """Command set for health checking."""


if __name__ == "__main__":
    main()
