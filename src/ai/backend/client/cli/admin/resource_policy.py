import json
import sys

import click

from ai.backend.cli.interaction import ask_yn
from ai.backend.cli.params import OptionalType
from ai.backend.cli.types import ExitCode, Undefined, undefined
from ai.backend.common.types import VFolderHostPermission

from ...func.keypair_resource_policy import (
    _default_detail_fields,
    _default_list_fields,
)
from ...session import Session
from ..extensions import pass_ctx_obj
from ..pretty import print_info
from ..types import CLIContext

# from ai.backend.client.output.fields import keypair_resource_policy_fields
from . import admin


@admin.group()
def keypair_resource_policy() -> None:
    """
    KeyPair resource policy administration commands.
    """


@keypair_resource_policy.command()
@pass_ctx_obj
@click.argument("name", type=str)
def info(ctx: CLIContext, name: str) -> None:
    """
    Show details about a keypair resource policy. When `name` option is omitted, the
    resource policy for the current access_key will be returned.
    """
    with Session() as session:
        try:
            rp = session.KeypairResourcePolicy(session.config.access_key)
            item = rp.info(name)
            ctx.output.print_item(item, _default_detail_fields)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@keypair_resource_policy.command()
@pass_ctx_obj
def list(ctx: CLIContext) -> None:
    """
    List and manage keypair resource policies.
    (admin privilege required)
    """
    with Session() as session:
        try:
            items = session.KeypairResourcePolicy.list()
            ctx.output.print_list(items, _default_list_fields)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@keypair_resource_policy.command()
@pass_ctx_obj
@click.argument("name", type=str, default=None, metavar="NAME")
@click.option(
    "--default-for-unspecified",
    type=str,
    default="UNLIMITED",
    help="Default behavior for unspecified resources: LIMITED, UNLIMITED",
)
@click.option(
    "--total-resource-slots",
    type=str,
    default="{}",
    help="Set total resource slots.",
)
@click.option(
    "--max-session-lifetime",
    type=int,
    default=0,
    help="Maximum lifetime to keep session alive.",
)
@click.option(
    "--max-concurrent-sessions",
    type=int,
    default=30,
    help="Number of maximum concurrent sessions.",
)
@click.option(
    "--max-concurrent-sftp-sessions",
    type=int,
    default=30,
    help="Number of maximum concurrent SFTP sessions.",
)
@click.option(
    "--max-containers-per-session",
    type=int,
    default=1,
    help="Number of maximum containers per session.",
)
@click.option(
    "--idle-timeout",
    type=int,
    default=1800,
    help="The maximum period of time allowed for kernels to wait further requests.",
)
@click.option(
    "--vfolder-host-perms",
    "--vfolder-host-permissions",
    "--vfhost-perms",
    "--allowed-vfolder-hosts",  # legacy name
    type=str,
    default=json.dumps({
        "local:volume1": [perm.value for perm in VFolderHostPermission],
    }),
    help=(
        "Allowed virtual folder hosts and permissions for them. It must be JSON string (e.g:"
        ' --vfolder-host-perms=\'{"HOST_NAME": ["create-vfolder", "modify-vfolder"]}\')'
    ),
)
@click.option(
    "--max-pending-session-count",
    type=int,
    default=None,
    help="Number of maximum pending sessions.",
)
@click.option(
    "--max-pending-session-resource-slots",
    type=str,
    default=None,
    help="Set maximum resource slots for pending sessions.",
)
def add(
    ctx: CLIContext,
    name: str,
    default_for_unspecified: str,
    total_resource_slots: str,  # JSON string
    max_session_lifetime: int,
    max_concurrent_sessions: int,
    max_concurrent_sftp_sessions: int,
    max_containers_per_session: int,
    idle_timeout: int,
    vfolder_host_perms: str,  # JSON string
    max_pending_session_count: int,
    max_pending_session_resource_slots: str,  # JSON string
) -> None:
    """
    Add a new keypair resource policy.

    NAME: NAME of a new keypair resource policy.
    """
    with Session() as session:
        try:
            data = session.KeypairResourcePolicy.create(
                name,
                default_for_unspecified=default_for_unspecified,
                total_resource_slots=total_resource_slots,
                max_session_lifetime=max_session_lifetime,
                max_concurrent_sessions=max_concurrent_sessions,
                max_concurrent_sftp_sessions=max_concurrent_sftp_sessions,
                max_containers_per_session=max_containers_per_session,
                idle_timeout=idle_timeout,
                vfolder_host_perms=vfolder_host_perms,
                max_pending_session_count=max_pending_session_count,
                max_pending_session_resource_slots=max_pending_session_resource_slots,
            )
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name="resource_policy",
                action_name="add",
            )
            sys.exit(ExitCode.FAILURE)
        if not data["ok"]:
            ctx.output.print_mutation_error(
                msg=data["msg"],
                item_name="resource_policy",
                action_name="add",
            )
            sys.exit(ExitCode.FAILURE)
        ctx.output.print_mutation_result(
            data,
            item_name="resource_policy",
        )


@keypair_resource_policy.command()
@pass_ctx_obj
@click.argument("name", type=str, default=None, metavar="NAME")
@click.option(
    "--default-for-unspecified",
    type=OptionalType(str),
    default=undefined,
    help="Default behavior for unspecified resources: LIMITED, UNLIMITED",
)
@click.option(
    "--total-resource-slots",
    type=OptionalType(str),
    default=undefined,
    help="Set total resource slots.",
)
@click.option(
    "--max-session-lifetime",
    type=OptionalType(int),
    default=undefined,
    help="Maximum lifetime to keep session alive.",
)
@click.option(
    "--max-concurrent-sessions",
    type=OptionalType(int),
    default=undefined,
    help="Number of maximum concurrent sessions.",
)
@click.option(
    "--max-concurrent-sftp-sessions",
    type=OptionalType(int),
    default=undefined,
    help="Number of maximum concurrent SFTP sessions.",
)
@click.option(
    "--max-containers-per-session",
    type=OptionalType(int),
    default=undefined,
    help="Number of maximum containers per session.",
)
@click.option(
    "--idle-timeout",
    type=OptionalType(int),
    default=undefined,
    help="The maximum period of time allowed for kernels to wait further requests.",
)
@click.option(
    "--vfolder-host-perms",
    "--vfolder-host-permissions",
    "--vfhost-perms",
    "--allowed-vfolder-hosts",  # legacy name
    type=OptionalType(str),
    default=undefined,
    help=(
        "Allowed virtual folder hosts. It must be JSON string (e.g:"
        ' --vfolder-host-perms=\'{"HOST_NAME": ["create-vfolder", "modify-vfolder"]}\')'
    ),
)
@click.option(
    "--max-pending-session-count",
    type=OptionalType(int),
    default=undefined,
    help="Number of maximum pending sessions.",
)
@click.option(
    "--max-pending-session-resource-slots",
    type=OptionalType(str),
    default=undefined,
    help="Set maximum resource slots for pending sessions.",
)
def update(
    ctx: CLIContext,
    name: str,
    default_for_unspecified: str | Undefined,
    total_resource_slots: str | Undefined,  # JSON string
    max_session_lifetime: int | Undefined,
    max_concurrent_sessions: int | Undefined,
    max_concurrent_sftp_sessions: int | Undefined,
    max_containers_per_session: int | Undefined,
    idle_timeout: int | Undefined,
    vfolder_host_perms: str | Undefined,  # JSON string
    max_pending_session_count: int | Undefined,
    max_pending_session_resource_slots: str | Undefined,  # JSON string
) -> None:
    """
    Update an existing keypair resource policy.

    NAME: NAME of a keypair resource policy to update.
    """
    with Session() as session:
        try:
            data = session.KeypairResourcePolicy.update(
                name,
                default_for_unspecified=default_for_unspecified,
                total_resource_slots=total_resource_slots,
                max_session_lifetime=max_session_lifetime,
                max_concurrent_sessions=max_concurrent_sessions,
                max_concurrent_sftp_sessions=max_concurrent_sftp_sessions,
                max_containers_per_session=max_containers_per_session,
                idle_timeout=idle_timeout,
                vfolder_host_perms=vfolder_host_perms,
                max_pending_session_count=max_pending_session_count,
                max_pending_session_resource_slots=max_pending_session_resource_slots,
            )
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name="resource_policy",
                action_name="update",
            )
            sys.exit(ExitCode.FAILURE)
        if not data["ok"]:
            ctx.output.print_mutation_error(
                msg=data["msg"],
                item_name="resource_policy",
                action_name="update",
            )
            sys.exit(ExitCode.FAILURE)
        ctx.output.print_mutation_result(
            data,
            extra_info={
                "name": name,
            },
        )


@keypair_resource_policy.command()
@pass_ctx_obj
@click.argument("name", type=str, metavar="NAME")
def delete(ctx: CLIContext, name: str) -> None:
    """
    Delete a keypair resource policy.

    NAME: NAME of a keypair resource policy to delete.
    """
    with Session() as session:
        if not ask_yn():
            print_info("Cancelled.")
            sys.exit(ExitCode.FAILURE)
        try:
            data = session.KeypairResourcePolicy.delete(name)
        except Exception as e:
            ctx.output.print_mutation_error(
                e,
                item_name="resource_policy",
                action_name="deletion",
            )
            sys.exit(ExitCode.FAILURE)
        if not data["ok"]:
            ctx.output.print_mutation_error(
                msg=data["msg"],
                item_name="resource_policy",
                action_name="deletion",
            )
            sys.exit(ExitCode.FAILURE)
        ctx.output.print_mutation_result(
            data,
            extra_info={
                "name": name,
            },
        )
