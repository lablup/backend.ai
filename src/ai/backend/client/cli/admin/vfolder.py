from __future__ import annotations

import sys

import click
import humanize
from tabulate import tabulate

from ai.backend.client.session import Session
from ai.backend.client.func.vfolder import _default_list_fields
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

    @click.pass_obj
    @click.option('-g', '--group', type=str, default=None,
                help='Filter by group ID.')
    @click.option('--filter', 'filter_', default=None,
                help='Set the query filter expression.')
    @click.option('--order', default=None,
                help='Set the query ordering expression.')
    @click.option('--offset', default=0,
                help='The index of the current page start for pagination.')
    @click.option('--limit', default=None,
                help='The page size for pagination.')
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
            sys.exit(1)

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
            print("Default vfolder host: {}".format(resp['default']))
            print("Mounted hosts: {}".format(', '.join(resp['allowed'])))
        except Exception as e:
            print_error(e)
            sys.exit(1)


@vfolder.command()
@click.argument('vfolder_host')
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
            print(tabulate(
                [(k, humanize.naturalsize(v, binary=True) if 'bytes' in k else f"{v:.2f}")
                 for k, v in resp['metric'].items()],
                headers=('Key', 'Value'),
            ))
        except Exception as e:
            print_error(e)
            sys.exit(1)


@vfolder.command()
@click.option('-a', '--agent-id', type=str, default=None,
              help='Target agent to fetch fstab contents.')
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
            sys.exit(1)
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
            sys.exit(1)
        print('manager')
        for k, v in resp['manager'].items():
            print(' ', k, ':', v)
        print('\nagents')
        for aid, data in resp['agents'].items():
            print(' ', aid)
            for k, v in data.items():
                print('   ', k, ':', v)


@vfolder.command()
@click.argument('fs-location', type=str)
@click.argument('name', type=str)
@click.option('-o', '--options', type=str, default=None, help='Mount options.')
@click.option('--edit-fstab', is_flag=True,
              help='Edit fstab file to mount permanently.')
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
            sys.exit(1)
        print('manager')
        for k, v in resp['manager'].items():
            print(' ', k, ':', v)
        print('agents')
        for aid, data in resp['agents'].items():
            print(' ', aid)
            for k, v in data.items():
                print('   ', k, ':', v)


@vfolder.command()
@click.argument('name', type=str)
@click.option('--edit-fstab', is_flag=True,
              help='Edit fstab file to mount permanently.')
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
            sys.exit(1)
        print('manager')
        for k, v in resp['manager'].items():
            print(' ', k, ':', v)
        print('agents')
        for aid, data in resp['agents'].items():
            print(' ', aid)
            for k, v in data.items():
                print('   ', k, ':', v)
