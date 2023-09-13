from __future__ import annotations

import sys

import click

from ai.backend.cli.interaction import ask_yn
from ai.backend.cli.types import ExitCode
from ai.backend.client.output.fields import user_fields
from ai.backend.client.session import Session

from ..extensions import pass_ctx_obj
from ..params import CommaSeparatedListType
from ..pretty import print_info
from ..types import CLIContext
from . import admin

list_expr = CommaSeparatedListType()


@admin.group()
def user() -> None:
    """
    User administration commands.
    """


@user.command()
@pass_ctx_obj
@click.option("-e", "--email", type=str, default=None, help="Email of a user to display.")
def info(ctx: CLIContext, email: str) -> None:
    """
    Show the information about the given user by email. If email is not give,
    requester's information will be displayed.
    """
    fields = [
        user_fields["uuid"],
        user_fields["username"],
        user_fields["role"],
        user_fields["email"],
        user_fields["full_name"],
        user_fields["need_password_change"],
        user_fields["status"],
        user_fields["status_info"],
        user_fields["created_at"],
        user_fields["domain_name"],
        user_fields["groups"],
        user_fields["allowed_client_ip"],
        user_fields["sudo_session_enabled"],
    ]
    with Session() as session:
        try:
            item = session.User.detail(email=email, fields=fields)
            ctx.output.print_item(item, fields=fields)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@user.command()
@pass_ctx_obj
@click.option(
    "-s",
    "--status",
    type=str,
    default=None,
    help="Filter users in a specific state (active, inactive, deleted, before-verification).",
)
@click.option(
    "-g",
    "--group",
    type=str,
    default=None,
    help="""
    Filter by group ID.

    \b
    EXAMPLE
        --group "$(backend.ai admin group list | grep 'example-group-name' | awk '{print $1}')"
    """,
)
@click.option(
    "--filter",
    "filter_",
    default=None,
    help="""
    Set the query filter expression.

    \b
    COLUMNS
        uuid, username, role, email, full_name, need_password_change,
        status, status_info, created_at, modified_at, domain_name, allowed_client_ip

    \b
    OPERATORS
        Binary Operators: ==, !=, <, <=, >, >=, is, isnot, like, ilike(case-insensitive), in, contains
        Condition Operators: &, |
        Special Symbol: % (wildcard for like and ilike operators)

    \b
    EXAMPLE QUERIES
        --filter 'status == "ACTIVE" & role in ["ADMIN", "SUPERADMIN"]'
        --filter 'created_at >= "2021-01-01" & created_at < "2023-01-01"'
        --filter 'email ilike "%@example.com"'
    """,
)
@click.option(
    "--order",
    default=None,
    help="""
    Set the query ordering expression.

    \b
    COLUMNS
        uuid, username, role, email, full_name, need_password_change,
        status, status_info, created_at, modified_at, domain_name

    \b
    OPTIONS
        ascending order (default): (+)column_name
        descending order: -column_name

    \b
    EXAMPLE
        --order 'uuid'
        --order '+uuid'
        --order '-created_at'
    """,
)
@click.option("--offset", default=0, help="The index of the current page start for pagination.")
@click.option("--limit", type=int, default=None, help="The page size for pagination.")
def list(ctx: CLIContext, status, group, filter_, order, offset, limit) -> None:
    """
    List users.
    (admin privilege required)
    """
    fields = [
        user_fields["uuid"],
        user_fields["username"],
        user_fields["role"],
        user_fields["email"],
        user_fields["full_name"],
        user_fields["need_password_change"],
        user_fields["status"],
        user_fields["status_info"],
        user_fields["created_at"],
        user_fields["domain_name"],
        user_fields["groups"],
        user_fields["allowed_client_ip"],
        user_fields["sudo_session_enabled"],
    ]
    try:
        with Session() as session:
            fetch_func = lambda pg_offset, pg_size: session.User.paginated_list(
                status,
                group,
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


@user.command()
@pass_ctx_obj
@click.argument("domain_name", type=str, metavar="DOMAIN_NAME")
@click.argument("email", type=str, metavar="EMAIL")
@click.argument("password", type=str, metavar="PASSWORD")
@click.option("-u", "--username", type=str, default="", help="Username.")
@click.option("-n", "--full-name", type=str, default="", help="Full name.")
@click.option(
    "-r",
    "--role",
    type=str,
    default="user",
    help="Role of the user. One of (admin, user, monitor).",
)
@click.option(
    "-s",
    "--status",
    type=str,
    default="active",
    help="Account status. One of (active, inactive, deleted, before-verification).",
)
@click.option(
    "--need-password-change",
    is_flag=True,
    help=(
        "Flag indicate that user needs to change password. "
        "Useful when admin manually create password."
    ),
)
@click.option(
    "--allowed-ip",
    type=list_expr,
    default=None,
    help=(
        "Allowed client IP. IPv4 and IPv6 are allowed. CIDR type is recommended. "
        '(e.g., --allowed-ip "127.0.0.1","127.0.0.2",...)'
    ),
)
@click.option("--description", type=str, default="", help="Description of the user.")
@click.option(
    "--sudo-session-enabled",
    is_flag=True,
    default=False,
    help=(
        "Enable passwordless sudo for a user inside a compute session. "
        "Note that this feature does not automatically install sudo for the session."
    ),
)
def add(
    ctx: CLIContext,
    domain_name,
    email,
    password,
    username,
    full_name,
    role,
    status,
    need_password_change,
    allowed_ip,
    description,
    sudo_session_enabled,
):
    """
    Add new user. A user must belong to a domain, so DOMAIN_NAME should be provided.

    \b
    DOMAIN_NAME: Name of the domain where new user belongs to.
    EMAIL: Email of new user.
    PASSWORD: Password of new user.
    """
    with Session() as session:
        try:
            data = session.User.create(
                domain_name,
                email,
                password,
                username=username,
                full_name=full_name,
                role=role,
                status=status,
                need_password_change=need_password_change,
                allowed_client_ip=allowed_ip,
                description=description,
                sudo_session_enabled=sudo_session_enabled,
            )
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name="user",
                action_name="add",
            )
            sys.exit(ExitCode.FAILURE)
        if not data["ok"]:
            ctx.output.print_mutation_error(
                msg=data["msg"],
                item_name="user",
                action_name="add",
            )
            sys.exit(ExitCode.FAILURE)
        ctx.output.print_mutation_result(
            data,
            item_name="user",
        )


@user.command()
@pass_ctx_obj
@click.argument("email", type=str, metavar="EMAIL")
@click.option("-p", "--password", type=str, help="Password.")
@click.option("-u", "--username", type=str, help="Username.")
@click.option("-n", "--full-name", type=str, help="Full name.")
@click.option("-d", "--domain-name", type=str, help="Domain name.")
@click.option(
    "-r",
    "--role",
    type=str,
    help="Role of the user. One of (admin, user, monitor).",
)
@click.option(
    "-s",
    "--status",
    type=str,
    help="Account status. One of (active, inactive, deleted, before-verification).",
)
@click.option(
    "--need-password-change",
    is_flag=True,
    help=(
        "Flag indicate that user needs to change password. "
        "Useful when admin manually create password."
    ),
)
@click.option(
    "--allowed-ip",
    type=list_expr,
    default=None,
    help=(
        "Allowed client IP. IPv4 and IPv6 are allowed. CIDR type is recommended. "
        '(e.g., --allowed-ip "127.0.0.1","127.0.0.2",...)'
    ),
)
@click.option("--description", type=str, default="", help="Description of the user.")
@click.option(
    "--sudo-session-enabled",
    is_flag=True,
    default=False,
    help=(
        "Enable passwordless sudo for a user inside a compute session. "
        "Note that this feature does not automatically install sudo for the session."
    ),
)
def update(
    ctx: CLIContext,
    email,
    password,
    username,
    full_name,
    domain_name,
    role,
    status,
    need_password_change,
    allowed_ip,
    description,
    sudo_session_enabled,
):
    """
    Update an existing user.

    \b
    EMAIL: Email of user to update.
    """
    with Session() as session:
        try:
            data = session.User.update(
                email,
                password=password,
                username=username,
                full_name=full_name,
                domain_name=domain_name,
                role=role,
                status=status,
                need_password_change=need_password_change,
                allowed_client_ip=allowed_ip,
                description=description,
                sudo_session_enabled=sudo_session_enabled,
            )
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name="user",
                action_name="update",
            )
            sys.exit(ExitCode.FAILURE)
        if not data["ok"]:
            ctx.output.print_mutation_error(
                msg=data["msg"],
                item_name="user",
                action_name="update",
            )
            sys.exit(ExitCode.FAILURE)
        ctx.output.print_mutation_result(
            data,
            extra_info={
                "email": email,
            },
        )


@user.command()
@pass_ctx_obj
@click.argument("email", type=str, metavar="EMAIL")
def delete(ctx: CLIContext, email):
    """
    Inactivate an existing user.

    \b
    EMAIL: Email of user to inactivate.
    """
    with Session() as session:
        try:
            data = session.User.delete(email)
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name="user",
                action_name="deletion",
            )
            sys.exit(ExitCode.FAILURE)
        if not data["ok"]:
            ctx.output.print_mutation_error(
                msg=data["msg"],
                item_name="user",
                action_name="deletion",
            )
            sys.exit(ExitCode.FAILURE)
        ctx.output.print_mutation_result(
            data,
            extra_info={
                "email": email,
            },
        )


@user.command()
@pass_ctx_obj
@click.argument("email", type=str, metavar="EMAIL")
@click.option(
    "--purge-shared-vfolders",
    is_flag=True,
    default=False,
    help=(
        "Delete user's all virtual folders. "
        "If False, shared folders will not be deleted "
        "and migrated the ownership to the requested admin."
    ),
)
def purge(ctx: CLIContext, email, purge_shared_vfolders):
    """
    Delete an existing user. This action cannot be undone.

    \b
    NAME: Name of a domain to delete.
    """
    with Session() as session:
        try:
            if not ask_yn():
                print_info("Cancelled")
                sys.exit(ExitCode.FAILURE)
            data = session.User.purge(email, purge_shared_vfolders)
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name="user",
                action_name="purge",
            )
            sys.exit(ExitCode.FAILURE)
        if not data["ok"]:
            ctx.output.print_mutation_error(
                msg=data["msg"],
                item_name="user",
                action_name="purge",
            )
            sys.exit(ExitCode.FAILURE)
        ctx.output.print_mutation_result(
            data,
            extra_info={
                "email": email,
            },
        )
