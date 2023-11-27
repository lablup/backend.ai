import asyncio
import sys

from tabulate import tabulate

from ai.backend.cli.types import ExitCode

from ...request import Request
from ...session import AsyncSession
from ..pretty import print_done, print_error, print_warn
from . import admin


@admin.group()
def license() -> None:
    """
    License administration commands.
    """


@license.command()
def show():
    """
    Show the license information (enterprise editions only).
    """

    async def _show_license():
        async with AsyncSession():
            rqst = Request("GET", "/license")
            async with rqst.fetch() as resp:
                data = await resp.json()
            if data["status"] == "valid":
                print_done("Your Backend.AI license is valid.")
                print(tabulate([(k, v) for k, v in data["certificate"].items()]))
            else:
                print_warn("Your Backend.AI license is valid.")

    try:
        asyncio.run(_show_license())
    except Exception as e:
        print_error(e)
        sys.exit(ExitCode.FAILURE)
