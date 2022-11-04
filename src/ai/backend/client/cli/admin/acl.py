import sys

from ai.backend.cli.types import ExitCode
from ai.backend.client.func.acl import _default_list_fields
from ai.backend.client.session import Session

from ..extensions import pass_ctx_obj
from ..types import CLIContext
from . import admin


@admin.group()
def permission():
    """
    Permission administration commands.
    """


@permission.command()
@pass_ctx_obj
def list(ctx: CLIContext) -> None:
    """
    List atomic permissions.
    """
    with Session() as session:
        try:
            items = session.Permission.list()
            ctx.output.print_item(items, _default_list_fields)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)
