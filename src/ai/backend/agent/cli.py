import asyncio
import pathlib
from pathlib import Path

import click
from tabulate import tabulate

from ai.backend.agent.config import get_agent_cfg
from ai.backend.agent.server import agent_local_config_iv
from ai.backend.cli.types import CliContextInfo
from ai.backend.common import config
from ai.backend.common.types import LogSeverity


@click.group()
def main():
    """The root entrypoint for unified CLI of agent"""
    pass


async def inspect_agent_status(cli_ctx: CliContextInfo, agent_pid: int) -> None:
    command = f"ps -p '{agent_pid}' -f"
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
    "--config-path",
    "--config",
    type=click.Path(
        file_okay=True,
        dir_okay=False,
        exists=True,
        path_type=pathlib.Path,
    ),
    default=None,
    help="The config file path. (default: ./agent.toml and /etc/backend.ai/agent.toml)",
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
    Collect and print each agent process's status.
    """
    cfg = config.check(get_agent_cfg(config_path, log_level, debug), agent_local_config_iv)
    pid_filepath = cfg["agent"]["pid-file"]

    with open(pid_filepath, "r") as file:
        agent_pid = int(file.read())

    asyncio.run(inspect_agent_status(cli_ctx, agent_pid))
