import sys

import click

from ai.backend.cli.params import BoolExprType, OptionalType
from ai.backend.cli.types import ExitCode, Undefined, undefined

from ...output.fields import keypair_fields
from ...session import Session
from ..extensions import pass_ctx_obj
from ..types import CLIContext
from . import admin


@admin.group()
def keypair() -> None:
    """
    KeyPair administration commands.
    """


@keypair.command()
@pass_ctx_obj
def info(ctx: CLIContext) -> None:
    """
    Show the server-side information of the currently configured access key.
    """
    fields = [
        keypair_fields["user_id"],
        keypair_fields["full_name"],
        keypair_fields["access_key"],
        keypair_fields["secret_key"],
        keypair_fields["is_active"],
        keypair_fields["is_admin"],
        keypair_fields["created_at"],
        keypair_fields["last_used"],
        keypair_fields["resource_policy"],
        keypair_fields["rate_limit"],
        keypair_fields["concurrency_used"],
    ]
    with Session() as session:
        try:
            kp = session.KeyPair(session.config.access_key)
            item = kp.info(fields=fields)
            ctx.output.print_item(item, fields)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@keypair.command()
@pass_ctx_obj
@click.option(
    "-u",
    "--user-id",
    type=str,
    default=None,
    help="Show keypairs of this given user. [default: show all]",
)
@click.option(
    "--is-active",
    type=OptionalType(BoolExprType),
    default=None,
    help="Filter keypairs by activation.",
)
@click.option("--filter", "filter_", default=None, help="Set the query filter expression.")
@click.option("--order", default=None, help="Set the query ordering expression.")
@click.option("--offset", default=0, help="The index of the current page start for pagination.")
@click.option("--limit", type=int, default=None, help="The page size for pagination.")
def list(ctx: CLIContext, user_id, is_active, filter_, order, offset, limit) -> None:
    """
    List keypairs.
    To show all keypairs or other user's, your access key must have the admin
    privilege.
    (admin privilege required)
    """
    fields = [
        keypair_fields["user_id"],
        keypair_fields["projects"],
        keypair_fields["full_name"],
        keypair_fields["access_key"],
        keypair_fields["secret_key"],
        keypair_fields["is_active"],
        keypair_fields["is_admin"],
        keypair_fields["created_at"],
        keypair_fields["last_used"],
        keypair_fields["resource_policy"],
        keypair_fields["rate_limit"],
        keypair_fields["concurrency_used"],
    ]
    try:
        with Session() as session:
            fetch_func = lambda pg_offset, pg_size: session.KeyPair.paginated_list(
                is_active,
                user_id=user_id,
                fields=fields,
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
        ctx.output.print_error(e)
        sys.exit(ExitCode.FAILURE)


@keypair.command()
@pass_ctx_obj
@click.argument("user-id", type=str, default=None, metavar="USERID")
@click.argument("resource-policy", type=str, default=None, metavar="RESOURCE_POLICY")
@click.option(
    "-a",
    "--admin",
    is_flag=True,
    help="Give the admin privilege to the new keypair.",
)
@click.option(
    "-i",
    "--inactive",
    is_flag=True,
    help="Create the new keypair in inactive state.",
)
@click.option(
    "-r",
    "--rate-limit",
    type=int,
    default=5000,
    help="Set the API query rate limit.",
)
def add(
    ctx: CLIContext,
    user_id: str,
    resource_policy: str,
    admin: bool,
    inactive: bool,
    rate_limit: int,
) -> None:
    """
    Add a new keypair.

    USER_ID: User ID of a new key pair.
    RESOURCE_POLICY: resource policy for new key pair.
    """
    with Session() as session:
        try:
            data = session.KeyPair.create(
                user_id,
                is_active=not inactive,
                is_admin=admin,
                resource_policy=resource_policy,
                rate_limit=rate_limit,
            )
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name="keypair",
                action_name="add",
            )
            sys.exit(ExitCode.FAILURE)
        if not data["ok"]:
            ctx.output.print_mutation_error(
                msg=data["msg"],
                item_name="keypair",
                action_name="add",
            )
            sys.exit(ExitCode.FAILURE)
        ctx.output.print_mutation_result(
            data,
            item_name="keypair",
            extra_info={
                "access_key": data["keypair"]["access_key"],
                "secret_key": data["keypair"]["secret_key"],
            },
        )


@keypair.command()
@pass_ctx_obj
@click.argument("access_key", type=str, metavar="ACCESSKEY")
@click.option(
    "--resource-policy",
    type=OptionalType(str),
    default=undefined,
    help="Resource policy for the keypair.",
)
@click.option(
    "--is-admin",
    type=OptionalType(BoolExprType),
    default=undefined,
    help="Set admin privilege.",
)
@click.option(
    "--is-active",
    type=OptionalType(BoolExprType),
    default=undefined,
    help="Set key pair active or not.",
)
@click.option(
    "-r",
    "--rate-limit",
    type=OptionalType(int),
    default=undefined,
    help="Set the API query rate limit.",
)
def update(
    ctx: CLIContext,
    access_key: str,
    resource_policy: str | Undefined,
    is_admin: bool | Undefined,
    is_active: bool | Undefined,
    rate_limit: int | Undefined,
) -> None:
    """
    Update an existing keypair.

    ACCESS_KEY: Access key of an existing key pair.
    """
    with Session() as session:
        try:
            data = session.KeyPair.update(
                access_key,
                is_active=is_active,
                is_admin=is_admin,
                resource_policy=resource_policy,
                rate_limit=rate_limit,
            )
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name="keypair",
                action_name="update",
            )
            sys.exit(ExitCode.FAILURE)
        if not data["ok"]:
            ctx.output.print_mutation_error(
                msg=data["msg"],
                item_name="keypair",
                action_name="update",
            )
            sys.exit(ExitCode.FAILURE)
        ctx.output.print_mutation_result(
            data,
            extra_info={
                "access_key": access_key,
            },
        )


@keypair.command()
@pass_ctx_obj
@click.argument("access-key", type=str, metavar="ACCESSKEY")
def delete(ctx: CLIContext, access_key: str) -> None:
    """
    Delete an existing keypair.

    ACCESSKEY: ACCESSKEY for a keypair to delete.
    """
    with Session() as session:
        try:
            data = session.KeyPair.delete(access_key)
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name="keypair",
                action_name="deletion",
            )
            sys.exit(ExitCode.FAILURE)
        if not data["ok"]:
            ctx.output.print_mutation_error(
                msg=data["msg"],
                item_name="keypair",
                action_name="deletion",
            )
            sys.exit(ExitCode.FAILURE)
        ctx.output.print_mutation_result(
            data,
            extra_info={
                "access_key": access_key,
            },
        )


@keypair.command()
@pass_ctx_obj
@click.argument("access-key", type=str, metavar="ACCESSKEY")
def activate(ctx: CLIContext, access_key: str) -> None:
    """
    Activate an inactivated keypair.

    ACCESS_KEY: Access key of an existing key pair.
    """
    with Session() as session:
        try:
            data = session.KeyPair.activate(access_key)
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name="keypair",
                action_name="activation",
            )
            sys.exit(ExitCode.FAILURE)
        if not data["ok"]:
            ctx.output.print_mutation_error(
                msg=data["msg"],
                item_name="keypair",
                action_name="activation",
            )
            sys.exit(ExitCode.FAILURE)
        ctx.output.print_mutation_result(
            data,
            extra_info={
                "access_key": access_key,
            },
        )


@keypair.command()
@pass_ctx_obj
@click.argument("access-key", type=str, metavar="ACCESSKEY")
def deactivate(ctx: CLIContext, access_key: str) -> None:
    """
    Deactivate an active keypair.

    ACCESS_KEY: Access key of an existing key pair.
    """
    with Session() as session:
        try:
            data = session.KeyPair.deactivate(access_key)
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name="keypair",
                action_name="deactivation",
            )
            sys.exit(ExitCode.FAILURE)
        if not data["ok"]:
            ctx.output.print_mutation_error(
                msg=data["msg"],
                item_name="keypair",
                action_name="deactivation",
            )
            sys.exit(ExitCode.FAILURE)
        ctx.output.print_mutation_result(
            data,
            extra_info={
                "access_key": access_key,
            },
        )
