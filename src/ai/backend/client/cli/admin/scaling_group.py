import sys

import click

from ai.backend.cli.params import BoolExprType, JSONParamType, OptionalType
from ai.backend.cli.types import ExitCode, Undefined, undefined
from ai.backend.client.func.scaling_group import _default_detail_fields, _default_list_fields
from ai.backend.client.output.fields import scaling_group_fields
from ai.backend.client.session import Session

from ..extensions import pass_ctx_obj
from ..types import CLIContext
from . import admin


@admin.group()
def scaling_group() -> None:
    """
    Scaling group (resource group) administration commands.
    """


@scaling_group.command()
@pass_ctx_obj
@click.argument("group", type=str, metavar="GROUP_NAME")
def get_available(ctx: CLIContext, group: str) -> None:
    with Session() as session:
        try:
            items = session.ScalingGroup.list_available(group)
            ctx.output.print_list(items, [scaling_group_fields["name"]])
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@scaling_group.command()
@pass_ctx_obj
@click.argument("name", type=str)
def info(ctx: CLIContext, name: str) -> None:
    """
    Show the information about the given scaling group.
    (superadmin privilege required)
    """
    with Session() as session:
        try:
            item = session.ScalingGroup.detail(name=name)
            ctx.output.print_item(item, _default_detail_fields)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@scaling_group.command()
@pass_ctx_obj
def list(ctx: CLIContext) -> None:
    """
    List and manage scaling groups.
    (superadmin privilege required)
    """
    with Session() as session:
        try:
            items = session.ScalingGroup.list()
            ctx.output.print_list(items, _default_list_fields)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@scaling_group.command()
@pass_ctx_obj
@click.argument("name", type=str, metavar="NAME")
@click.option(
    "-d",
    "--description",
    "--desc",
    type=str,
    default="",
    help="Description of new scaling group.",
)
@click.option("--inactive", is_flag=True, help="New scaling group will be inactive.")
@click.option(
    "--private",
    is_flag=True,
    help=(
        "New scaling group will be private. "
        "Private scaling groups cannot be used when users create new sessions."
    ),
)
@click.option("--driver", type=str, default="static", help="Set driver.")
@click.option(
    "--driver-opts",
    type=JSONParamType(),
    default="{}",
    help="Set driver options as a JSON string.",
)
@click.option("--scheduler", type=str, default="fifo", help="Set scheduler.")
@click.option(
    "--scheduler-opts",
    type=JSONParamType(),
    default="{}",
    help="""
        Set scheduler options as a JSON string.
        If the 'allowed_session_types' key is not specified, the policy defaults to accept both 'interactive' and 'batch'.
        """,
)
@click.option(
    "--use-host-network",
    is_flag=True,
    help="If true, run containers on host networking mode.",
)
@click.option("--wsproxy-addr", type=str, default=None, help="Set app proxy address.")
@click.option("--wsproxy-api-token", type=str, default=None, help="Set app proxy API token.")
def add(
    ctx: CLIContext,
    name: str,
    description: str,
    inactive: bool,
    private: bool,
    driver: str,
    driver_opts: dict[str, str] | Undefined,
    scheduler: str,
    scheduler_opts: dict[str, str] | Undefined,
    use_host_network: bool,
    wsproxy_addr: str,
    wsproxy_api_token: str,
):
    """
    Add a new scaling group.

    NAME: Name of new scaling group.
    """
    with Session() as session:
        try:
            data = session.ScalingGroup.create(
                name,
                description=description,
                is_active=not inactive,
                is_public=not private,
                driver=driver,
                driver_opts=driver_opts,
                scheduler=scheduler,
                scheduler_opts=scheduler_opts,
                use_host_network=use_host_network,
                wsproxy_addr=wsproxy_addr,
                wsproxy_api_token=wsproxy_api_token,
            )
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name="scaling_group",
                action_name="add",
            )
            sys.exit(ExitCode.FAILURE)
        if not data["ok"]:
            ctx.output.print_mutation_error(
                msg=data["msg"],
                item_name="scaling_group",
                action_name="add",
            )
            sys.exit(ExitCode.FAILURE)
        ctx.output.print_mutation_result(
            data,
            item_name="scaling_group",
        )


@scaling_group.command()
@pass_ctx_obj
@click.argument("name", type=str, metavar="NAME")
@click.option(
    "-d",
    "--description",
    "--desc",
    type=OptionalType(str),
    default=undefined,
    help="Description of new scaling group.",
)
@click.option(
    "-a",
    "--active",
    type=OptionalType(BoolExprType),
    default=undefined,
    help="Change the active/inactive status if specified.",
)
@click.option(
    "--private",
    type=OptionalType(BoolExprType),
    default=undefined,
    help="Change the private status if specified",
)
@click.option(
    "--driver",
    type=OptionalType(str),
    default=undefined,
    help="Set driver.",
)
@click.option(
    "--driver-opts",
    type=OptionalType(JSONParamType),
    default=undefined,
    help="Set driver options as a JSON string.",
)
@click.option(
    "--scheduler",
    type=OptionalType(str),
    default=undefined,
    help="Set scheduler.",
)
@click.option(
    "--scheduler-opts",
    type=OptionalType(JSONParamType),
    default=undefined,
    help="""
        Set scheduler options as a JSON string.
        If the 'allowed_session_types' key is not specified, the policy defaults to accept both 'interactive' and 'batch'.
        """,
)
@click.option(
    "--use-host-network",
    type=OptionalType(BoolExprType),
    default=undefined,
    help="Change the host-networking mode if specified.",
)
@click.option(
    "--wsproxy-addr",
    type=OptionalType(str),
    default=undefined,
    help="Set app proxy address.",
)
@click.option(
    "--wsproxy-api-token",
    type=OptionalType(str),
    default=undefined,
    help="Set app proxy API token.",
)
def update(
    ctx: CLIContext,
    name: str,
    description: str | Undefined,
    active: bool | Undefined,
    private: bool | Undefined,
    driver: str | Undefined,
    driver_opts: dict | Undefined,
    scheduler: str | Undefined,
    scheduler_opts: dict | Undefined,
    use_host_network: bool | Undefined,
    wsproxy_addr: str | Undefined,
    wsproxy_api_token: str | Undefined,
):
    """
    Update existing scaling group.

    NAME: Name of new scaling group.
    """
    with Session() as session:
        try:
            data = session.ScalingGroup.update(
                name,
                description=description,
                is_active=active,
                is_public=not private if private is not undefined else undefined,
                driver=driver,
                driver_opts=driver_opts,
                scheduler=scheduler,
                scheduler_opts=scheduler_opts,
                use_host_network=use_host_network,
                wsproxy_addr=wsproxy_addr,
                wsproxy_api_token=wsproxy_api_token,
            )
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name="scaling_group",
                action_name="update",
            )
            sys.exit(ExitCode.FAILURE)
        if not data["ok"]:
            ctx.output.print_mutation_error(
                msg=data["msg"],
                item_name="scaling_group",
                action_name="update",
            )
            sys.exit(ExitCode.FAILURE)
        ctx.output.print_mutation_result(
            data,
            extra_info={
                "name": name,
            },
        )


@scaling_group.command()
@pass_ctx_obj
@click.argument("name", type=str, metavar="NAME")
def delete(ctx: CLIContext, name):
    """
    Delete an existing scaling group.

    NAME: Name of a scaling group to delete.
    """
    with Session() as session:
        try:
            data = session.ScalingGroup.delete(name)
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name="scaling_group",
                action_name="deletion",
            )
            sys.exit(ExitCode.FAILURE)
        if not data["ok"]:
            ctx.output.print_mutation_error(
                msg=data["msg"],
                item_name="scaling_group",
                action_name="deletion",
            )
            sys.exit(ExitCode.FAILURE)
        ctx.output.print_mutation_result(
            data,
            extra_info={
                "name": name,
            },
        )


@scaling_group.command()
@pass_ctx_obj
@click.argument("scaling_group", type=str, metavar="SCALING_GROUP")
@click.argument("domain", type=str, metavar="DOMAIN")
def associate_scaling_group(ctx: CLIContext, scaling_group, domain):
    """
    Associate a domain with a scaling_group.

    \b
    SCALING_GROUP: The name of a scaling group.
    DOMAIN: The name of a domain.
    """
    with Session() as session:
        try:
            data = session.ScalingGroup.associate_domain(scaling_group, domain)
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name="scaling_group",
                action_name="scaling_group_association",
            )
            sys.exit(ExitCode.FAILURE)
        if not data["ok"]:
            ctx.output.print_mutation_error(
                msg=data["msg"],
                item_name="scaling_group",
                action_name="scaling_group_association",
            )
            sys.exit(ExitCode.FAILURE)
        ctx.output.print_mutation_result(
            data,
            extra_info={
                "detail_msg": "Scaling group {} is associated with domain {}.".format(
                    scaling_group, domain
                ),
            },
        )


@scaling_group.command()
@pass_ctx_obj
@click.argument("scaling_group", type=str, metavar="SCALING_GROUP")
@click.argument("domain", type=str, metavar="DOMAIN")
def dissociate_scaling_group(ctx: CLIContext, scaling_group, domain):
    """
    Dissociate a domain from a scaling_group.

    \b
    SCALING_GROUP: The name of a scaling group.
    DOMAIN: The name of a domain.
    """
    with Session() as session:
        try:
            data = session.ScalingGroup.dissociate_domain(scaling_group, domain)
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name="scaling_group",
                action_name="scaling_group_dissociation",
            )
            sys.exit(ExitCode.FAILURE)
        if not data["ok"]:
            ctx.output.print_mutation_error(
                msg=data["msg"],
                item_name="scaling_group",
                action_name="scaling_group_dissociation",
            )
            sys.exit(ExitCode.FAILURE)
        ctx.output.print_mutation_result(
            data,
            item_name="scaling_group",
            extra_info={
                "detail_msg": "Scaling group {} is dissociated from domain {}.".format(
                    scaling_group, domain
                ),
            },
        )
