import sys

import click

# from ai.backend.client.output.fields import image_fields
from ai.backend.cli.main import main
from ai.backend.cli.types import ExitCode
from ai.backend.client.func.image import _default_list_fields_admin
from ai.backend.client.output.fields import image_fields
from ai.backend.client.session import Session

from .extensions import pass_ctx_obj
from .pretty import print_done, print_error, print_fail
from .types import CLIContext


@main.group()
def image() -> None:
    """
    Image commands.
    """


@image.command()
@pass_ctx_obj
@click.option("--customized", is_flag=True, help="Get images customized by user only")
def list(ctx: CLIContext, customized: bool) -> None:
    """
    Show the list of registered images in this cluster.
    """
    with Session() as session:
        try:
            if customized:
                fields = (
                    image_fields["customized_image_name"],
                    image_fields["id"],
                    image_fields["name"],
                    image_fields["registry"],
                    image_fields["architecture"],
                    image_fields["tag"],
                    image_fields["size_bytes"],
                )
                items = session.Image.list_customized(fields=fields)
            else:
                fields = _default_list_fields_admin
                items = session.Image.list(fields=fields)
            ctx.output.print_list(items, fields)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@image.command()
@click.argument("reference_or_id", type=str)
@click.option("--arch", type=str, default=None, help="Set an explicit architecture.")
def forget(reference_or_id, arch):
    """Forget image from server. This command will only work for image customized by user
    unless callee has superadmin privileges.

    REFERENCE_OR_ID: Canonical string of image (<registry>/<project>/<name>:<tag>)"""
    with Session() as session:
        try:
            try:
                result = session.Image.forget_image_by_id(reference_or_id)
            except Exception:
                if not arch:
                    print_fail(
                        "`arch` option should be set when removing image via its reference string"
                    )
                    sys.exit(ExitCode.FAILURE)
                result = session.Image.forget_image(reference_or_id, arch)
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)
        if result["ok"]:
            print_done(f"Image forgotten: {reference_or_id}")
        else:
            print_fail("Image forget has failed: {0}".format(result["msg"]))
