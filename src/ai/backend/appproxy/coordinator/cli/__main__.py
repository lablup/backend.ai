import asyncio
import importlib
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

import aiohttp_cors
import click
import tomli_w
from aiohttp import web
from setproctitle import setproctitle

from ai.backend.appproxy.common.config import generate_example_json
from ai.backend.appproxy.common.openapi import generate_openapi
from ai.backend.appproxy.common.utils import ensure_json_serializable
from ai.backend.cli.types import ExitCode
from ai.backend.logging import BraceStyleAdapter, LogLevel

from ..config import ServerConfig
from .context import CLIContext

log = BraceStyleAdapter(logging.getLogger("ai.backend.manager.cli"))


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
    help="The config file path. (default: ./manager.conf and /etc/backend.ai/manager.conf)",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Set the logging level to DEBUG",
)
@click.option(
    "--log-level",
    type=click.Choice([*LogLevel], case_sensitive=False),
    default=LogLevel.NOTSET,
    help="Set the logging verbosity level",
)
@click.pass_context
def main(
    ctx: click.Context,
    debug: bool,
    log_level: LogLevel,
    config_path: Optional[Path] = None,
) -> None:
    """
    Proxy Coordinator Administration CLI
    """
    setproctitle("backend.ai: proxy-coordinator.cli")
    if debug:
        log_level = LogLevel.DEBUG
    ctx.obj = ctx.with_resource(CLIContext(config_path=config_path, log_level=log_level))


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
    if output == "-" or output is None:
        print(tomli_w.dumps(ensure_json_serializable(generate_example_json(ServerConfig))))
    else:
        with open(output, mode="w") as fw:
            fw.write(tomli_w.dumps(ensure_json_serializable(generate_example_json(ServerConfig))))


async def _generate() -> dict[str, Any]:
    from ..server import global_subapp_pkgs

    cors_options = {
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=False, expose_headers="*", allow_headers="*"
        ),
    }

    subapps: list[web.Application] = []
    for subapp in global_subapp_pkgs:
        pkg = importlib.import_module("ai.backend.appproxy.coordinator.api" + subapp)
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


@main.command(
    context_settings=dict(
        ignore_unknown_options=True,
    )
)
@click.option(
    "--psql-container",
    "container_name",
    type=str,
    default=None,
    metavar="ID_OR_NAME",
    help=(
        "Open a postgres client shell using the psql executable "
        "shipped with the given postgres container. "
        'If not set or set as an empty string "", it will auto-detect '
        "the psql container from the halfstack. "
        'If set "-", it will use the host-provided psql executable. '
        "You may append additional arguments passed to the psql cli command. "
        "[default: auto-detect from halfstack]"
    ),
)
@click.option(
    "--psql-help",
    is_flag=True,
    help="Show the help text of the psql command instead of this dbshell command.",
)
@click.argument("psql_args", nargs=-1, type=click.UNPROCESSED)
@click.pass_obj
def dbshell(cli_ctx: CLIContext, container_name, psql_help, psql_args):
    """
    Run the database shell.

    All additional arguments and options except `--psql-container` and `--psql-help` are
    transparently forwarded to the psql command.
    For instance, you can use `-c` to execute a psql/SQL statement on the command line.

    Note that you do not have to specify connection-related options
    because the dbshell command fills out them from the manager configuration.
    """
    db_config = cli_ctx.local_config.db
    if psql_help:
        psql_args = ["--help"]
    if not container_name:
        # Try to get the database container name of the halfstack
        candidate_container_names = subprocess.check_output(
            ["docker", "ps", "--format", "{{.Names}}", "--filter", "name=half-db"],
        )
        if not candidate_container_names:
            click.echo(
                "Could not find the halfstack postgres container. "
                "Please set the container name explicitly.",
                err=True,
            )
            sys.exit(ExitCode.FAILURE)
        container_name = None
        name_list = candidate_container_names.decode("utf-8").splitlines()
        for name in name_list:
            if "exporter" in name:
                continue  # Skip exporter containers
            container_name = name
            break
        if not container_name:
            click.echo(
                "Could not find the halfstack postgres container. "
                "Please set the container name explicitly.",
                err=True,
            )
            sys.exit(ExitCode.FAILURE)
    elif container_name == "-":
        # Use the host-provided psql command
        cmd = [
            "psql",
            (f"postgres://{db_config.user}:{db_config.password}@{db_config.addr}/{db_config.name}"),
            *psql_args,
        ]
        subprocess.run(cmd)
        return
    # Use the container to start the psql client command
    log.info(f"using the db container {container_name} ...")
    cmd = [
        "docker",
        "exec",
        "-i",
        "-t",
        container_name,
        "psql",
        "-U",
        db_config.user,
        "-d",
        db_config.name,
        *psql_args,
    ]
    subprocess.run(cmd)


if __name__ == "__main__":
    main()
