import json
import sys
from typing import Optional

import click

from ai.backend.cli.types import ExitCode
from ai.backend.client.func.image import _default_list_fields_admin
from ai.backend.client.session import Session
from ai.backend.common.bgtask.types import BgtaskStatus

from ...compat import asyncio_run
from ...session import AsyncSession
from ..extensions import pass_ctx_obj
from ..pretty import ProgressBarWithSpinner, print_done, print_error, print_fail, print_warn
from ..types import CLIContext
from . import admin


@admin.group()
def image() -> None:
    """
    Image administration commands.
    """


@image.command()
@pass_ctx_obj
@click.option("--operation", is_flag=True, help="Get operational images only")
def list(ctx: CLIContext, operation: bool) -> None:
    """
    Show the list of registered images in this cluster.
    """
    with Session() as session:
        try:
            items = session.Image.list(operation=operation)
            ctx.output.print_list(items, _default_list_fields_admin)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@image.command()
@click.option(
    "-r",
    "--registry",
    type=str,
    default=None,
    help='The name (usually hostname or "lablup") of the Docker registry configured.',
)
@click.option(
    "-p",
    "--project",
    type=str,
    default=None,
    help="The name of the project to which the images belong. If not specified, scan all projects.",
)
def rescan(registry: str, project: Optional[str] = None) -> None:
    """
    Update the kernel image metadata from the configured registries.
    """

    async def rescan_images_impl(registry: str, project: Optional[str]) -> None:
        async with AsyncSession() as session:
            try:
                result = await session.Image.rescan_images(registry, project)
            except Exception as e:
                print_error(e)
                sys.exit(ExitCode.FAILURE)
            if not result["ok"]:
                print_fail(f"Failed to scan registries: {result['msg']}")
                sys.exit(ExitCode.FAILURE)
            print_done("Started updating the image metadata from the configured registries.")
            bgtask_id = result["task_id"]
            bgtask = session.BackgroundTask(bgtask_id)
            completion_msg_func = lambda: print_done("Finished registry scanning.")
            try:
                async with (
                    bgtask.listen_events() as response,
                    ProgressBarWithSpinner("Scanning the registry...", unit="images") as pbar,
                ):
                    async for ev in response:
                        data = json.loads(ev.data)
                        match ev.event:
                            case BgtaskStatus.UPDATED:
                                pbar.total = data["total_progress"]
                                pbar.write(data["message"])
                                pbar.update(data["current_progress"] - pbar.n)
                            case BgtaskStatus.FAILED:
                                error_msg = data["message"]
                                completion_msg_func = lambda: print_fail(
                                    f"Error occurred: {error_msg}"
                                )
                            case BgtaskStatus.CANCELLED:
                                completion_msg_func = lambda: print_warn(
                                    "Registry scanning has been cancelled in the middle."
                                )
                            # TODO: Remove "bgtask_done" from the condition after renaming BgtaskPartialSuccess event name.
                            case BgtaskStatus.PARTIAL_SUCCESS | BgtaskStatus.DONE:
                                errors = data.get("errors")
                                if errors:
                                    for error in errors:
                                        print_fail(f"Error reported: {error}")
                                    completion_msg_func = lambda: print_warn(
                                        f"Finished registry scanning with {len(errors)} issues."
                                    )
            finally:
                completion_msg_func()

    asyncio_run(rescan_images_impl(registry, project))


@image.command()
@click.argument("alias", type=str)
@click.argument("target", type=str)
@click.option("--arch", type=str, default=None, help="Set an explicit architecture.")
def alias(alias, target, arch):
    """Add an image alias."""
    with Session() as session:
        try:
            result = session.Image.alias_image(alias, target, arch)
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)
        if result["ok"]:
            print_done(f"An alias has created: {alias} -> {target}")
        else:
            print_fail("Aliasing has failed: {0}".format(result["msg"]))


@image.command()
@click.argument("alias", type=str)
def dealias(alias):
    """Remove an image alias."""
    with Session() as session:
        try:
            result = session.Image.dealias_image(alias)
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)
        if result["ok"]:
            print_done(f"The alias has been removed: {alias}")
        else:
            print_fail("Dealiasing has failed: {0}".format(result["msg"]))
