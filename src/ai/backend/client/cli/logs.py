import sys

import click

from ai.backend.cli.main import main
from ai.backend.cli.types import ExitCode

from ..compat import asyncio_run
from ..session import AsyncSession
from .pretty import print_error


@main.command()
@click.argument("task_id", metavar="TASKID")
def task_logs(task_id):
    """
    Shows the output logs of a batch task.

    \b
    TASKID: An UUID of a task (or kernel).
    """

    async def _task_logs():
        async with AsyncSession() as session:
            async for chunk in session.ComputeSession.get_task_logs(task_id):
                print(chunk.decode("utf8", errors="replace"), end="")

    try:
        asyncio_run(_task_logs())
    except Exception as e:
        print_error(e)
        sys.exit(ExitCode.FAILURE)
