import sys

import click

from ai.backend.cli.main import main
from ai.backend.cli.types import ExitCode
from ai.backend.client.session import Session

from .extensions import pass_ctx_obj
from .params import ByteSizeParamCheckType
from .pretty import print_done, print_error
from .types import CLIContext


@main.group()
def model():
    """Set of model operations"""


@model.command()
@pass_ctx_obj
@click.option("--filter", "filter_", default=None, help="Set the query filter expression.")
@click.option("--order", default=None, help="Set the query ordering expression.")
@click.option("--offset", default=0, help="The index of the current page start for pagination.")
@click.option("--limit", type=int, default=None, help="The page size for pagination.")
def list(ctx: CLIContext, filter_, order, offset, limit):
    """
    List models.
    """

    with Session() as session:
        try:
            fetch_func = lambda pg_offset, pg_size: session.Model.paginated_list(
                page_offset=pg_offset,
                page_size=pg_size,
                filter=filter_,
                order=order,
            )
            ctx.output.print_paginated_list(
                fetch_func,
                initial_page_offset=offset,
                page_size=limit,
            )
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)


@model.command()
@click.argument("model_id", metavar="MODEL", type=str)
def info(model_id):
    """
    Info models.
    """

    with Session() as session:
        try:
            result = session.Model(model_id).info()
            print("Model info")
            print("- ID: {0}".format(result["id"]))
            print("- Name: {0}".format(result["name"]))
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)


@model.command()
@click.argument("name", type=str)
@click.argument("host", type=str, default=None)
@click.option(
    "-g",
    "--group",
    metavar="GROUP",
    type=str,
    default=None,
    help="Group ID or NAME.",
)
@click.option(
    "--unmanaged",
    "host_path",
    type=bool,
    is_flag=True,
    help="Treats HOST as a mount point of unmanaged model. "
    "This option can only be used by Admin or Superadmin.",
)
@click.option(
    "-p",
    "--permission",
    metavar="PERMISSION",
    type=str,
    default="rw",
    help="Folder's innate permission. "
    'Group folders can be shared as read-only by setting this option to "ro".'
    "Invited folders override this setting by its own invitation permission.",
)
@click.option(
    "-q",
    "--quota",
    metavar="QUOTA",
    type=ByteSizeParamCheckType(),
    default="0",
    help="Quota of the virtual folder. "
    "(Use 'm' for megabytes, 'g' for gigabytes, and etc.) "
    "Default is maximum amount possible.",
)
@click.option(
    "--cloneable",
    "--allow-clone",
    type=bool,
    is_flag=True,
    help="Allows the virtual folder to be cloned by users.",
)
def create(name, host, group, host_path, permission, quota, cloneable):
    """
    Create model.
    """
    with Session() as session:
        try:
            if host_path:
                result = session.Model.create(
                    name=name,
                    unmanaged_path=host,
                    group=group,
                    permission=permission,
                    quota=quota,
                    cloneable=cloneable,
                )
            else:
                result = session.Model.create(
                    name=name,
                    host=host,
                    group=group,
                    permission=permission,
                    quota=quota,
                    cloneable=cloneable,
                )
            print_done("Model created.")
            print(f"ID: {result['id']}")
            print(f"Name: {result['name']}")
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)


@model.command()
@click.argument("model_id", metavar="MODEL", type=str)
def rm(model_id):
    """
    Remove model.

    \b
    MODEL: Model ID.
    """

    with Session() as session:
        try:
            serving = session.Model(model_id)
            serving.delete()
            print_done("Model deleted.")
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)
