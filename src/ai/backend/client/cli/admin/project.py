import sys
import uuid

import click

from ai.backend.cli.interaction import ask_yn
from ai.backend.cli.types import ExitCode
from ai.backend.client.func.project import _default_detail_fields, _default_list_fields
from ai.backend.client.session import Session

from ..extensions import pass_ctx_obj
from ..pretty import print_info
from ..types import CLIContext

# from ai.backend.client.output.fields import project_fields
from . import admin


@admin.group()
def project() -> None:
    """
    User project administration commands
    """


@project.command()
@pass_ctx_obj
@click.argument("id_or_name", type=str)
def info(ctx: CLIContext, id_or_name: str) -> None:
    """
    Show the information about the project(s) having the given name.
    Two or more projects in different domains may have the same name,
    so this may print out information of multiple projects if queried
    by a superadmin.

    When queried with a human-readable name by a super-admin,
    it may return multiple results with the same name from
    different domains.

    \b
    id_or_name: Project ID (UUID) or name.
    """
    with Session() as session:
        try:
            gid = uuid.UUID(id_or_name)
        except ValueError:
            # interpret as name
            try:
                item = session.Project.from_name(id_or_name)
                ctx.output.print_item(item, _default_detail_fields)
            except Exception as e:
                ctx.output.print_error(e)
                sys.exit(ExitCode.FAILURE)
        else:
            # interpret as UUID
            try:
                item = session.Project.detail(gid=str(gid))
                ctx.output.print_item(item, _default_detail_fields)
            except Exception as e:
                ctx.output.print_error(e)
                sys.exit(ExitCode.FAILURE)


@project.command()
@pass_ctx_obj
@click.option(
    "-d",
    "--domain-name",
    type=str,
    default=None,
    help="Domain name to list projects belongs to it.",
)
def list(ctx: CLIContext, domain_name) -> None:
    """
    List projects in the given domain.
    (admin privilege required)
    """
    with Session() as session:
        try:
            items = session.Project.list(domain_name=domain_name)
            ctx.output.print_list(items, _default_list_fields)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@project.command()
@pass_ctx_obj
@click.argument("domain_name", type=str, metavar="DOMAIN_NAME")
@click.argument("name", type=str, metavar="NAME")
@click.option("-d", "--description", type=str, default="", help="Description of new project.")
@click.option("-i", "--inactive", is_flag=True, help="New project will be inactive.")
@click.option("--total-resource-slots", type=str, default="{}", help="Set total resource slots.")
@click.option(
    "--allowed-vfolder-hosts",
    type=str,
    default="{}",
    help="Allowed virtual folder hosts. "
    'It must be JSON string (e.g: --allowed-vfolder-hosts=\'{"HOST_NAME": ["create-vfolder", "modify-vfolder"]}\')',
)
def add(
    ctx: CLIContext,
    domain_name,
    name,
    description,
    inactive,
    total_resource_slots,
    allowed_vfolder_hosts,
):
    """
    Add new project. A project must belong to a domain, so DOMAIN_NAME should be provided.

    \b
    DOMAIN_NAME: Name of the domain where new project belongs to.
    NAME: Name of new project.
    """
    with Session() as session:
        try:
            data = session.Project.create(
                domain_name,
                name,
                description=description,
                is_active=not inactive,
                total_resource_slots=total_resource_slots,
                allowed_vfolder_hosts=allowed_vfolder_hosts,
            )
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name="project",
                action_name="add",
            )
            sys.exit(ExitCode.FAILURE)
        if not data["ok"]:
            ctx.output.print_mutation_error(
                msg=data["msg"],
                item_name="project",
                action_name="add",
            )
            sys.exit(ExitCode.FAILURE)
        ctx.output.print_mutation_result(
            data,
            item_name="project",
        )


@project.command()
@pass_ctx_obj
@click.argument("gid", type=str, metavar="GROUP_ID")
@click.option("-n", "--name", type=str, help="New name of the project")
@click.option("-d", "--description", type=str, help="Description of the project")
@click.option("--is-active", type=bool, help="Set project inactive.")
@click.option("--total-resource-slots", type=str, help="Update total resource slots.")
@click.option(
    "--allowed-vfolder-hosts",
    type=str,
    help="Allowed virtual folder hosts. "
    'It must be JSON string (e.g: --allowed-vfolder-hosts=\'{"HOST_NAME": ["create-vfolder", "modify-vfolder"]}\')',
)
def update(
    ctx: CLIContext, gid, name, description, is_active, total_resource_slots, allowed_vfolder_hosts
):
    """
    Update an existing project. Domain name is not necessary since project ID is unique.

    GROUP_ID: Project ID to update.
    """
    with Session() as session:
        try:
            data = session.Project.update(
                gid,
                name=name,
                description=description,
                is_active=is_active,
                total_resource_slots=total_resource_slots,
                allowed_vfolder_hosts=allowed_vfolder_hosts,
            )
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name="project",
                action_name="update",
            )
            sys.exit(ExitCode.FAILURE)
        if not data["ok"]:
            ctx.output.print_mutation_error(
                msg=data["msg"],
                item_name="project",
                action_name="update",
            )
            sys.exit(ExitCode.FAILURE)
        ctx.output.print_mutation_result(
            data,
            extra_info={
                "gid": gid,
            },
        )


@project.command()
@pass_ctx_obj
@click.argument("gid", type=str, metavar="GROUP_ID")
def delete(ctx: CLIContext, gid):
    """
    Inactivates the existing project. Does not actually delete it for safety.

    GROUP_ID: Project ID to inactivate.
    """
    with Session() as session:
        try:
            data = session.Project.delete(gid)
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name="project",
                action_name="deletion",
            )
            sys.exit(ExitCode.FAILURE)
        if not data["ok"]:
            ctx.output.print_mutation_error(
                msg=data["msg"],
                item_name="project",
                action_name="deletion",
            )
            sys.exit(ExitCode.FAILURE)
        ctx.output.print_mutation_result(
            data,
            extra_info={
                "gid": gid,
            },
        )


@project.command()
@pass_ctx_obj
@click.argument("gid", type=str, metavar="GROUP_ID")
def purge(ctx: CLIContext, gid):
    """
    Delete the existing project. This action cannot be undone.

    GROUP_ID: Project ID to inactivate.
    """
    with Session() as session:
        try:
            if not ask_yn():
                print_info("Cancelled")
                sys.exit(ExitCode.FAILURE)
            data = session.Project.purge(gid)
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name="project",
                action_name="purge",
            )
            sys.exit(ExitCode.FAILURE)
        if not data["ok"]:
            ctx.output.print_mutation_error(
                msg=data["msg"],
                item_name="project",
                action_name="purge",
            )
            sys.exit(ExitCode.FAILURE)
        ctx.output.print_mutation_result(
            data,
            extra_info={
                "gid": gid,
            },
        )


@project.command()
@pass_ctx_obj
@click.argument("gid", type=str, metavar="GROUP_ID")
@click.argument("user_uuids", type=str, metavar="USER_UUIDS", nargs=-1)
def add_users(ctx: CLIContext, gid, user_uuids):
    """
    Add users to a project.

    \b
    GROUP_ID: Project ID where users will be belong to.
    USER_UUIDS: List of users' uuids to be added to the project.
    """
    with Session() as session:
        try:
            data = session.Project.add_users(gid, user_uuids)
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name="project",
                action_name="add_users",
            )
            sys.exit(ExitCode.FAILURE)
        if not data["ok"]:
            ctx.output.print_mutation_error(
                msg=data["msg"],
                item_name="project",
                action_name="add_users",
            )
            sys.exit(ExitCode.FAILURE)
        ctx.output.print_mutation_result(
            data,
            extra_info={
                "gid": gid,
            },
        )


@project.command()
@pass_ctx_obj
@click.argument("gid", type=str, metavar="GROUP_ID")
@click.argument("user_uuids", type=str, metavar="USER_UUIDS", nargs=-1)
def remove_users(ctx: CLIContext, gid, user_uuids):
    """
    Remove users from a project.

    \b
    GROUP_ID: Project ID where users currently belong to.
    USER_UUIDS: List of users' uuids to be removed from the project.
    """
    with Session() as session:
        try:
            data = session.Project.remove_users(gid, user_uuids)
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name="project",
                action_name="users_remove",
            )
            sys.exit(ExitCode.FAILURE)
        if not data["ok"]:
            ctx.output.print_mutation_error(
                msg=data["msg"],
                item_name="project",
                action_name="users_remove",
            )
            sys.exit(ExitCode.FAILURE)
        ctx.output.print_mutation_result(
            data,
            extra_info={
                "gid": gid,
            },
        )
