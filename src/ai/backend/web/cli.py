import asyncio
import sys
from pathlib import Path
from pprint import pformat

import click
from tabulate import tabulate

from ai.backend.cli.types import CliContextInfo
from ai.backend.common.exception import ConfigurationError
from ai.backend.common.types import LogSeverity
from ai.backend.web.config import load_local_config


@click.group()
def main():
    """The root entrypoint for unified CLI of the web server"""
    pass


async def inspect_server_status(cli_ctx: CliContextInfo, webserver_pid: int) -> None:
    command = f"ps -p '{webserver_pid}' -f"
    process = await asyncio.create_subprocess_shell(command, stdout=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    if stderr:
        raise RuntimeError(f"Failed to execute the command: {command}")

    lines = stdout.decode().splitlines()
    process_list = []

    for line in lines[1:]:
        columns = line.split()
        # Combine all text following UID, PID, PPID, C, STIME, TTY, TIME into CMD
        process_info = columns[:7] + [" ".join(columns[7:])]
        process_list.append(process_info)

    print(tabulate(process_list, headers=lines[0].split(), tablefmt="pretty"))
    pass


@main.command()
@click.pass_obj
@click.option(
    "-f",
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default="webserver.conf",
    help="The config file path. (default: ./webserver.conf and /etc/backend.ai/webserver.conf)",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Set the logging level to DEBUG",
)
@click.option(
    "-s",
    "--systemctl",
    is_flag=True,
    help="Include the systemctl status command result in the output",
)
@click.option(
    "--log-level",
    type=click.Choice([*LogSeverity], case_sensitive=False),
    default=LogSeverity.INFO,
    help="Set the logging verbosity level",
)
def status(
    cli_ctx: CliContextInfo,
    config_path: Path,
    log_level: LogSeverity,
    debug: bool = False,
    systemctl: bool = False,
) -> None:
    """
    Collect and print each webserver process's status.
    """

    try:
        local_config = load_local_config(config_path, log_level, debug=debug)
    except ConfigurationError as e:
        print(
            "ConfigurationError: Could not read or validate the webserver local config.",
            file=sys.stderr,
        )
        print(pformat(e.invalid_data), file=sys.stderr)
        raise click.Abort()

    pid_filepath = local_config["webserver"]["pid-file"]

    if not pid_filepath.is_file():
        print(
            'ConfigurationError: "pid-file" not found in the configuration file.',
            file=sys.stderr,
        )
        raise click.Abort()

    with open(pid_filepath, "r") as file:
        agent_pid = int(file.read())

    asyncio.run(inspect_server_status(cli_ctx, agent_pid))
