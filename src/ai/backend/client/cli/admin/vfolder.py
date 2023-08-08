from __future__ import annotations

import sys

import click
import humanize
from tabulate import tabulate

from ai.backend.cli.types import ExitCode
from ai.backend.client.func.vfolder import _default_list_fields
from ai.backend.client.session import Session

from ..extensions import pass_ctx_obj
from ..pretty import print_error
from ..types import CLIContext
from ..vfolder import vfolder as user_vfolder
from . import admin


@admin.group()
def vfolder() -> None:
    """
    VFolder administration commands.
    """


def _list_cmd(docs: str = None):
    @pass_ctx_obj
    @click.option(
        "-g",
        "--group",
        type=str,
        default=None,
        help="""\b
        Filter by group ID.

        \b
        EXAMPLE
            --group "$(backend.ai admin group list | grep 'example-group-name' | awk '{print $1}')"

        \b
        """,
    )
    @click.option(
        "--filter",
        "filter_",
        default=None,
        help="""\b
        Set the query filter expression.

        \b
        COLUMNS
            host, name, created_at, creator,
            ownership_type (USER, GROUP),
            status (READY, PERFORMING, CLONING, DELETING, MOUNTED),
            permission (READ_ONLY, READ_WRITE, RW_DELETE, OWNER_PERM)

        \b
        OPERATORS
            Binary Operators: ==, !=, <, <=, >, >=, is, isnot, like, ilike(case-insensitive), in, contains
            Condition Operators: &, |
            Special Symbol: % (wildcard for like and ilike operators)

        \b
        EXAMPLE QUERIES
            --filter 'status == "READY" & permission in ["READ_ONLY", "READ_WRITE"]'
            --filter 'created_at >= "2021-01-01" & created_at < "2023-01-01"'
            --filter 'creator ilike "%@example.com"'

        \b
        """,
    )
    @click.option(
        "--order",
        default=None,
        help="""\b
        Set the query ordering expression.

        \b
        COLUMNS
            host, name, created_at, creator, ownership_type, status, permission

        \b
        OPTIONS
            ascending order (default): (+)column_name
            descending order: -column_name

        \b
        EXAMPLE
            --order 'host'
            --order '+host'
            --order '-created_at'

        \b
        """,
    )
    @click.option("--offset", default=0, help="The index of the current page start for pagination.")
    @click.option("--limit", type=int, default=None, help="The page size for pagination.")
    def list(ctx: CLIContext, group, filter_, order, offset, limit) -> None:
        """
        List virtual folders.
        """
        try:
            with Session() as session:
                fetch_func = lambda pg_offset, pg_size: session.VFolder.paginated_list(
                    group,
                    fields=_default_list_fields,
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

    if docs is not None:
        list.__doc__ = docs
    return list


user_vfolder.command()(_list_cmd())
vfolder.command()(_list_cmd())


@vfolder.command()
def list_hosts():
    """
    List all mounted hosts from virtual folder root.
    (superadmin privilege required)
    """
    with Session() as session:
        try:
            resp = session.VFolder.list_all_hosts()
            print("Default vfolder host: {}".format(resp["default"]))
            print("Mounted hosts: {}".format(", ".join(resp["allowed"])))
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)


@vfolder.command()
@click.argument("vfolder_host")
def perf_metric(vfolder_host):
    """
    Show the performance statistics of a vfolder host.
    (superadmin privilege required)

    A vfolder host consists of a string of the storage proxy name and the volume name
    separated by a colon. (e.g., "local:volume1")
    """
    with Session() as session:
        try:
            resp = session.VFolder.get_performance_metric(vfolder_host)
            print(
                tabulate(
                    [
                        (k, humanize.naturalsize(v, binary=True) if "bytes" in k else f"{v:.2f}")
                        for k, v in resp["metric"].items()
                    ],
                    headers=("Key", "Value"),
                )
            )
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)


@vfolder.command()
@click.option(
    "-a", "--agent-id", type=str, default=None, help="Target agent to fetch fstab contents."
)
def get_fstab_contents(agent_id):
    """
    Get contents of fstab file from a node.
    (superadmin privilege required)

    If agent-id is not specified, manager's fstab contents will be returned.
    """
    with Session() as session:
        try:
            resp = session.VFolder.get_fstab_contents(agent_id)
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)
        print(resp)


@vfolder.command()
def list_mounts():
    """
    List all mounted hosts in virtual folder root.
    (superadmin privilege required)
    """
    with Session() as session:
        try:
            resp = session.VFolder.list_mounts()
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)
        print("manager")
        for k, v in resp["manager"].items():
            print(" ", k, ":", v)
        print("\nagents")
        for aid, data in resp["agents"].items():
            print(" ", aid)
            for k, v in data.items():
                print("   ", k, ":", v)


@vfolder.command()
@click.argument("fs-location", type=str)
@click.argument("name", type=str)
@click.option("-o", "--options", type=str, default=None, help="Mount options.")
@click.option("--edit-fstab", is_flag=True, help="Edit fstab file to mount permanently.")
def mount_host(fs_location, name, options, edit_fstab):
    """
    Mount a host in virtual folder root.
    (superadmin privilege required)

    \b
    FS-LOCATION: Location of file system to be mounted.
    NAME: Name of mounted host.
    """
    with Session() as session:
        try:
            resp = session.VFolder.mount_host(name, fs_location, options, edit_fstab)
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)
        print("manager")
        for k, v in resp["manager"].items():
            print(" ", k, ":", v)
        print("agents")
        for aid, data in resp["agents"].items():
            print(" ", aid)
            for k, v in data.items():
                print("   ", k, ":", v)


@vfolder.command()
@click.argument("name", type=str)
@click.option("--edit-fstab", is_flag=True, help="Edit fstab file to mount permanently.")
def umount_host(name, edit_fstab):
    """
    Unmount a host from virtual folder root.
    (superadmin privilege required)

    \b
    NAME: Name of mounted host.
    """
    with Session() as session:
        try:
            resp = session.VFolder.umount_host(name, edit_fstab)
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)
        print("manager")
        for k, v in resp["manager"].items():
            print(" ", k, ":", v)
        print("agents")
        for aid, data in resp["agents"].items():
            print(" ", aid)
            for k, v in data.items():
                print("   ", k, ":", v)


@vfolder.command
def list_shared_vfolders():
    """
    List all shared vfolder.
    (superadmin privilege required)
    """
    with Session() as session:
        try:
            resp = session.VFolder.list_shared_vfolders()
            result = resp.get("shared", [])
            for _result in result:
                print(
                    'Virtual folder "{0}" (ID: {1})'.format(
                        _result["vfolder_name"], _result["vfolder_id"]
                    )
                )
                print("- Owner: {0}".format(_result["owner"]))
                print("- Status: {0}".format(_result["status"]))
                print("- Permission: {0}".format(_result["perm"]))
                print("- Folder Type: {0}".format(_result["type"]))
                shared_to = _result.get("shared_to", {})
                if shared_to:
                    print("- Shared to:")
                    for k, v in shared_to.items():
                        print("\t- {0}: {1}\n".format(k, v))
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)


@vfolder.command
@click.argument("vfolder_id", type=str)
def shared_vfolder_info(vfolder_id):
    """Show the vfolder permission information of the given virtual folder.

    \b
    VFOLDER_ID: ID of a virtual folder.
    """
    with Session() as session:
        try:
            resp = session.VFolder.shared_vfolder_info(vfolder_id)
            result = resp.get("shared", [])
            if result:
                _result = result[0]
                print(
                    'Virtual folder "{0}" (ID: {1})'.format(
                        _result["vfolder_name"], _result["vfolder_id"]
                    )
                )
                print("- Owner: {0}".format(_result["owner"]))
                print("- Status: {0}".format(_result["status"]))
                print("- Permission: {0}".format(_result["perm"]))
                print("- Folder Type: {0}".format(_result["type"]))
                shared_to = _result.get("shared_to", {})
                if shared_to:
                    print("- Shared to:")
                    for k, v in shared_to.items():
                        print("\t- {0}: {1}\n".format(k, v))
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)


@vfolder.command()
@click.argument("vfolder_id", type=str)
@click.argument("user_id", type=str)
@click.option(
    "-p", "--permission", type=str, metavar="PERMISSION", help="Folder's innate permission."
)
def update_shared_vf_permission(vfolder_id, user_id, permission):
    """
    Update permission for shared vfolders.

    \b
    VFOLDER_ID: ID of a virtual folder.
    USER_ID: ID of user who have been granted access to shared vFolder.
    PERMISSION: Permission to update. "ro" (read-only) / "rw" (read-write) / "wd" (write-delete).
    """
    with Session() as session:
        try:
            resp = session.VFolder.update_shared_vfolder(vfolder_id, user_id, permission)
            print("Updated.")
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)
        print(resp)


@vfolder.command()
@click.argument("vfolder_id", type=str)
@click.argument("user_id", type=str)
def remove_shared_vf_permission(vfolder_id, user_id):
    """
    Remove permission for shared vfolders.

    \b
    VFOLDER_ID: ID of a virtual folder.
    USER_ID: ID of user who have been granted access to shared vFolder.
    """
    with Session() as session:
        try:
            resp = session.VFolder.update_shared_vfolder(vfolder_id, user_id, None)
            print("Removed.")
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)
        print(resp)


@vfolder.command()
@click.argument("vfolder_id", type=str)
@click.argument("user_email", type=str)
def change_vfolder_ownership(vfolder_id, user_email):
    """
    Change the ownership of vfolder

    \b
    VFOLDER_ID: ID of a virtual folder.
    USER_EMAIL:  user email to have the ownership of current vfolder
    """
    with Session() as session:
        try:
            session.VFolder.change_vfolder_ownership(vfolder_id, user_email)
            print(f"Now ownership of VFolder:{vfolder_id} goes to User:{user_email}")
        except Exception as e:
            print_error(e)
            sys.exit(ExitCode.FAILURE)
