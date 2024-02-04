import sys
import uuid
from typing import Sequence

import click

from ai.backend.cli.interaction import ask_yn
from ai.backend.cli.params import BoolExprType, OptionalType
from ai.backend.cli.types import ExitCode, Undefined, undefined

from ...func.group import _default_detail_fields, _default_list_fields
from ...session import Session
from ..extensions import pass_ctx_obj
from ..pretty import print_info
from ..types import CLIContext

# from ai.backend.client.output.fields import group_fields
from . import admin


@admin.group()
def group() -> None:
    """
    User group (project) administration commands
    """


@group.command()
@pass_ctx_obj
@click.argument("id_or_name", type=str)
def info(ctx: CLIContext, id_or_name: str) -> None:
    """
    Show the information about the group(s) having the given name.
    Two or more groups in different domains may have the same name,
    so this may print out information of multiple groups if queried
    by a superadmin.

    When queried with a human-readable name by a super-admin,
    it may return multiple results with the same name from
    different domains.

    \b
    id_or_name: Group ID (UUID) or name.
    """
    with Session() as session:
        try:
            gid = uuid.UUID(id_or_name)
        except ValueError:
            # interpret as name
            try:
                groups = session.Group.from_name(id_or_name)
                item = groups[0]  # take the first one
                ctx.output.print_item(item, _default_detail_fields)
            except Exception as e:
                ctx.output.print_error(e)
                sys.exit(ExitCode.FAILURE)
        else:
            # interpret as UUID
            try:
                item = session.Group.detail(gid=str(gid))
                ctx.output.print_item(item, _default_detail_fields)
            except Exception as e:
                ctx.output.print_error(e)
                sys.exit(ExitCode.FAILURE)


@group.command()
@pass_ctx_obj
@click.option(
    "-d", "--domain-name", type=str, default=None, help="Domain name to list groups belongs to it."
)
def list(ctx: CLIContext, domain_name) -> None:
    """
    List groups in the given domain.
    (admin privilege required)
    """
    with Session() as session:
        try:
            items = session.Group.list(domain_name=domain_name)
            ctx.output.print_list(items, _default_list_fields)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@group.command()
@pass_ctx_obj
@click.argument("domain_name", type=str, metavar="DOMAIN_NAME")
@click.argument("name", type=str, metavar="NAME")
@click.option("-d", "--description", type=str, default="", help="Description of new group.")
@click.option("-i", "--inactive", is_flag=True, help="New group will be inactive.")
@click.option("--total-resource-slots", type=str, default="{}", help="Set total resource slots.")
@click.option(
    "--vfolder-host-perms",
    "--vfolder-host-permissions",
    "--vfhost-perms",
    "--allowed-vfolder-hosts",  # legacy name
    type=str,
    default="{}",
    help=(
        "Allowed virtual folder hosts and permissions for them. It must be JSON string (e.g:"
        ' --vfolder-host-perms=\'{"HOST_NAME": ["create-vfolder", "modify-vfolder"]}\')'
    ),
)
def add(
    ctx: CLIContext,
    domain_name: str,
    name: str,
    description: str,
    inactive: bool,
    total_resource_slots: str,  # JSON string
    vfolder_host_perms: str,  # JSON string
) -> None:
    """
    Add new group. A group must belong to a domain, so DOMAIN_NAME should be provided.

    \b
    DOMAIN_NAME: Name of the domain where new group belongs to.
    NAME: Name of new group.
    """
    with Session() as session:
        try:
            data = session.Group.create(
                domain_name,
                name,
                description=description,
                is_active=not inactive,
                total_resource_slots=total_resource_slots,
                allowed_vfolder_hosts=vfolder_host_perms,
            )
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name="group",
                action_name="add",
            )
            sys.exit(ExitCode.FAILURE)
        if not data["ok"]:
            ctx.output.print_mutation_error(
                msg=data["msg"],
                item_name="group",
                action_name="add",
            )
            sys.exit(ExitCode.FAILURE)
        ctx.output.print_mutation_result(
            data,
            item_name="group",
        )


@group.command()
@pass_ctx_obj
@click.argument("gid", type=str, metavar="GROUP_ID")
@click.option(
    "-n",
    "--name",
    type=OptionalType(str),
    default=undefined,
    help="New name of the group",
)
@click.option(
    "-d",
    "--description",
    type=OptionalType(str),
    default=undefined,
    help="Description of the group",
)
@click.option(
    "--is-active",
    type=OptionalType(BoolExprType),
    default=undefined,
    help="Set group inactive.",
)
@click.option(
    "--total-resource-slots",
    type=OptionalType(str),
    default=undefined,
    help="Update total resource slots.",
)
@click.option(
    "--vfolder-host-perms",
    "--vfolder-host-permissions",
    "--vfhost-perms",
    "--allowed-vfolder-hosts",  # legacy name
    type=OptionalType(str),
    default=undefined,
    help=(
        "Allowed virtual folder hosts and permissions for them. It must be JSON string (e.g:"
        ' --vfolder-host-perms=\'{"HOST_NAME": ["create-vfolder", "modify-vfolder"]}\')'
    ),
)
def update(
    ctx: CLIContext,
    gid: str | Undefined,
    name: str | Undefined,
    description: str | Undefined,
    is_active: bool | Undefined,
    total_resource_slots: str | Undefined,  # JSON string
    vfolder_host_perms: str | Undefined,  # JSON string
) -> None:
    """
    Update an existing group. Domain name is not necessary since group ID is unique.

    GROUP_ID: Group ID to update.
    """
    with Session() as session:
        try:
            data = session.Group.update(
                gid,
                name=name,
                description=description,
                is_active=is_active,
                total_resource_slots=total_resource_slots,
                allowed_vfolder_hosts=vfolder_host_perms,
            )
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name="group",
                action_name="update",
            )
            sys.exit(ExitCode.FAILURE)
        if not data["ok"]:
            ctx.output.print_mutation_error(
                msg=data["msg"],
                item_name="group",
                action_name="update",
            )
            sys.exit(ExitCode.FAILURE)
        ctx.output.print_mutation_result(
            data,
            extra_info={
                "gid": gid,
            },
        )


@group.command()
@pass_ctx_obj
@click.argument("gid", type=str, metavar="GROUP_ID")
def delete(ctx: CLIContext, gid: str) -> None:
    """
    Inactivates the existing group. Does not actually delete it for safety.

    GROUP_ID: Group ID to inactivate.
    """
    with Session() as session:
        try:
            data = session.Group.delete(gid)
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name="group",
                action_name="deletion",
            )
            sys.exit(ExitCode.FAILURE)
        if not data["ok"]:
            ctx.output.print_mutation_error(
                msg=data["msg"],
                item_name="group",
                action_name="deletion",
            )
            sys.exit(ExitCode.FAILURE)
        ctx.output.print_mutation_result(
            data,
            extra_info={
                "gid": gid,
            },
        )


@group.command()
@pass_ctx_obj
@click.argument("gid", type=str, metavar="GROUP_ID")
def purge(ctx: CLIContext, gid: str) -> None:
    """
    Delete the existing group. This action cannot be undone.

    GROUP_ID: Group ID to inactivate.
    """
    with Session() as session:
        try:
            if not ask_yn():
                print_info("Cancelled")
                sys.exit(ExitCode.FAILURE)
            data = session.Group.purge(gid)
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name="group",
                action_name="purge",
            )
            sys.exit(ExitCode.FAILURE)
        if not data["ok"]:
            ctx.output.print_mutation_error(
                msg=data["msg"],
                item_name="group",
                action_name="purge",
            )
            sys.exit(ExitCode.FAILURE)
        ctx.output.print_mutation_result(
            data,
            extra_info={
                "gid": gid,
            },
        )


@group.command()
@pass_ctx_obj
@click.argument("gid", type=str, metavar="GROUP_ID")
@click.argument("user_uuids", type=str, metavar="USER_UUIDS", nargs=-1)
def add_users(ctx: CLIContext, gid: str, user_uuids: Sequence[str]) -> None:
    """
    Add users to a group.

    \b
    GROUP_ID: Group ID where users will be belong to.
    USER_UUIDS: List of users' uuids to be added to the group.
    """
    with Session() as session:
        try:
            data = session.Group.add_users(gid, user_uuids)
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name="group",
                action_name="add_users",
            )
            sys.exit(ExitCode.FAILURE)
        if not data["ok"]:
            ctx.output.print_mutation_error(
                msg=data["msg"],
                item_name="group",
                action_name="add_users",
            )
            sys.exit(ExitCode.FAILURE)
        ctx.output.print_mutation_result(
            data,
            extra_info={
                "gid": gid,
            },
        )


@group.command()
@pass_ctx_obj
@click.argument("gid", type=str, metavar="GROUP_ID")
@click.argument("user_uuids", type=str, metavar="USER_UUIDS", nargs=-1)
def remove_users(ctx: CLIContext, gid: str, user_uuids: Sequence[str]) -> None:
    """
    Remove users from a group.

    \b
    GROUP_ID: Group ID where users currently belong to.
    USER_UUIDS: List of users' uuids to be removed from the group.
    """
    with Session() as session:
        try:
            data = session.Group.remove_users(gid, user_uuids)
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name="group",
                action_name="users_remove",
            )
            sys.exit(ExitCode.FAILURE)
        if not data["ok"]:
            ctx.output.print_mutation_error(
                msg=data["msg"],
                item_name="group",
                action_name="users_remove",
            )
            sys.exit(ExitCode.FAILURE)
        ctx.output.print_mutation_result(
            data,
            extra_info={
                "gid": gid,
            },
        )
