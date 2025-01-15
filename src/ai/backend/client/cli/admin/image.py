import json
import sys

import click

from ai.backend.cli.types import ExitCode
from ai.backend.client.func.image import _default_list_fields_admin
from ai.backend.client.session import Session

from ...compat import asyncio_run
from ...session import AsyncSession
from ..extensions import pass_ctx_obj
from ..pretty import ProgressViewer, print_done, print_error, print_fail, print_warn
from ..types import CLIContext

# from ai.backend.client.output.fields import image_fields
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
def rescan(registry: str) -> None:
    """
    Update the kernel image metadata from all configured docker registries.
    """

    async def rescan_images_impl(registry: str) -> None:
        async with AsyncSession() as session:
            try:
                result = await session.Image.rescan_images(registry)
            except Exception as e:
                print_error(e)
                sys.exit(ExitCode.FAILURE)
            if not result["ok"]:
                print_fail(f"Failed to begin registry scanning: {result['msg']}")
                sys.exit(ExitCode.FAILURE)
            print_done("Started updating the image metadata from the configured registries.")
            bgtask_id = result["task_id"]
            bgtask = session.BackgroundTask(bgtask_id)
            try:
                completion_msg_func = lambda: print_done("Finished registry scanning.")
                async with (
                    bgtask.listen_events() as response,
                    ProgressViewer("Scanning the registry...") as viewer,
                ):
                    async for ev in response:
                        data = json.loads(ev.data)
                        if ev.event == "bgtask_updated":
                            if viewer.tqdm is None:
                                pbar = await viewer.to_tqdm(unit="images")
                            else:
                                pbar.total = data["total_progress"]
                                pbar.write(data["message"])
                                pbar.update(data["current_progress"] - pbar.n)
                        elif ev.event == "bgtask_failed":
                            error_msg = data["message"]
                            completion_msg_func = lambda: print_fail(f"Error occurred: {error_msg}")
                        elif ev.event == "bgtask_cancelled":
                            completion_msg_func = lambda: print_warn(
                                "Registry scanning has been cancelled in the middle."
                            )
            finally:
                completion_msg_func()

    asyncio_run(rescan_images_impl(registry))


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
