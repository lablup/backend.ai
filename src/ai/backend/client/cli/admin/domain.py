import sys
from typing import Sequence

import click

from ai.backend.cli.interaction import ask_yn
from ai.backend.cli.params import BoolExprType, CommaSeparatedListType, OptionalType
from ai.backend.cli.types import ExitCode, Undefined, undefined

from ...func.domain import _default_detail_fields, _default_list_fields
from ...session import Session
from ..extensions import pass_ctx_obj
from ..pretty import print_info
from ..types import CLIContext

# from ai.backend.client.output.fields import domain_fields
from . import admin


@admin.group()
def domain():
    """
    Domain administration commands.
    """


@domain.command()
@pass_ctx_obj
@click.argument("name", type=str)
def info(ctx: CLIContext, name: str) -> None:
    """
    Show the information about the given domain.
    If name is not give, user's own domain information will be retrieved.
    """
    with Session() as session:
        try:
            item = session.Domain.detail(name=name)
            ctx.output.print_item(item, _default_detail_fields)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@domain.command()
@pass_ctx_obj
def list(ctx: CLIContext) -> None:
    """
    List and manage domains.
    (admin privilege required)
    """
    with Session() as session:
        try:
            items = session.Domain.list()
            ctx.output.print_list(items, _default_list_fields)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@domain.command()
@pass_ctx_obj
@click.argument("name", type=str, metavar="NAME")
@click.option("-d", "--description", type=str, default="", help="Description of new domain")
@click.option("--inactive", is_flag=True, help="New domain will be inactive.")
@click.option(
    "--total-resource-slots",
    type=str,
    default="{}",
    help="Set total resource slots as a JSON string.",
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
@click.option(
    "--allowed-docker-registries",
    type=OptionalType(CommaSeparatedListType),
    default=undefined,
    help="Allowed docker registries.",
)
def add(
    ctx: CLIContext,
    name: str,
    description: str,
    inactive: bool,
    total_resource_slots: str,
    vfolder_host_perms: str | Undefined,
    allowed_docker_registries: Sequence[str] | Undefined,
) -> None:
    """
    Add a new domain.

    NAME: Name of new domain.
    """
    with Session() as session:
        try:
            data = session.Domain.create(
                name,
                description=description,
                is_active=not inactive,
                total_resource_slots=total_resource_slots,
                vfolder_host_perms=vfolder_host_perms,
                allowed_docker_registries=allowed_docker_registries,
            )
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name="domain",
                action_name="add",
            )
            sys.exit(ExitCode.FAILURE)
        if not data["ok"]:
            ctx.output.print_mutation_error(
                msg=data["msg"],
                item_name="domain",
                action_name="add",
            )
            sys.exit(ExitCode.FAILURE)
        ctx.output.print_mutation_result(
            data,
            item_name="domain",
        )


@domain.command()
@pass_ctx_obj
@click.argument("name", type=str, metavar="NAME")
@click.option(
    "--new-name",
    type=OptionalType(str),
    default=undefined,
    help="New name of the domain",
)
@click.option(
    "--description",
    type=OptionalType(str),
    default=undefined,
    help="Set the description of the domain",
)
@click.option(
    "--is-active",
    type=OptionalType(BoolExprType),
    default=undefined,
    help="Change the active/inactive status if specified.",
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
@click.option(
    "--allowed-docker-registries",
    type=OptionalType(CommaSeparatedListType),
    default=undefined,
    help="Allowed docker registries.",
)
def update(
    ctx: CLIContext,
    name: str,
    new_name: str | Undefined,
    description: str | Undefined,
    is_active: bool | Undefined,
    total_resource_slots: str | Undefined,
    vfolder_host_perms: str | Undefined,
    allowed_docker_registries: Sequence[str] | Undefined,
) -> None:
    """
    Update an existing domain.

    NAME: Name of new domain.
    """
    with Session() as session:
        try:
            data = session.Domain.update(
                name,
                new_name=new_name,
                description=description,
                is_active=is_active,
                total_resource_slots=total_resource_slots,
                vfolder_host_perms=vfolder_host_perms,
                allowed_docker_registries=allowed_docker_registries,
            )
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name="domain",
                action_name="update",
            )
            sys.exit(ExitCode.FAILURE)
        if not data["ok"]:
            ctx.output.print_mutation_error(
                msg=data["msg"],
                item_name="domain",
                action_name="update",
            )
            sys.exit(ExitCode.FAILURE)
        ctx.output.print_mutation_result(
            data,
            extra_info={
                "name": name,
            },
        )


@domain.command()
@pass_ctx_obj
@click.argument("name", type=str, metavar="NAME")
def delete(ctx: CLIContext, name: str) -> None:
    """
    Deletes an existing domain. This action only deletes the primary record and might leave behind some associated data or metadata that can be manually cleaned up or ignored. Ideal for removing items that may be re-created or restored.

    NAME: Name of a domain to inactive.
    """
    with Session() as session:
        try:
            data = session.Domain.delete(name)
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name="domain",
                action_name="deletion",
            )
            sys.exit(ExitCode.FAILURE)
        if not data["ok"]:
            ctx.output.print_mutation_error(
                msg=data["msg"],
                item_name="domain",
                action_name="deletion",
            )
            sys.exit(ExitCode.FAILURE)
        ctx.output.print_mutation_result(
            data,
            extra_info={
                "name": name,
            },
        )


@domain.command()
@pass_ctx_obj
@click.argument("name", type=str, metavar="NAME")
def purge(ctx: CLIContext, name: str) -> None:
    """
    Purges an existing domain. This action is irreversible and should be used when you need to ensure that no trace of the resource remains.

    NAME: Name of a domain to delete.
    """
    with Session() as session:
        try:
            if not ask_yn():
                print_info("Cancelled")
                sys.exit(ExitCode.FAILURE)
            data = session.Domain.purge(name)
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name="domain",
                action_name="purge",
            )
            sys.exit(ExitCode.FAILURE)
        if not data["ok"]:
            ctx.output.print_mutation_error(
                msg=data["msg"],
                item_name="domain",
                action_name="purge",
            )
            sys.exit(ExitCode.FAILURE)
        ctx.output.print_mutation_result(
            data,
            extra_info={
                "name": name,
            },
        )
