from __future__ import annotations

import sys

import click

from ai.backend.client.session import Session
from ai.backend.client.output.fields import storage_fields
from . import admin
from ..types import CLIContext


@admin.group()
def storage() -> None:
    """
    Storage proxy administration commands.
    """


@storage.command()
@click.pass_obj
@click.argument('vfolder_host')
def info(ctx: CLIContext, vfolder_host: str) -> None:
    """
    Show the information about the given storage volume.
    (super-admin privilege required)
    """
    fields = [
        storage_fields['id'],
        storage_fields['backend'],
        storage_fields['capabilities'],
        storage_fields['path'],
        storage_fields['fsprefix'],
        storage_fields['hardware_metadata'],
        storage_fields['performance_metric'],
    ]
    with Session() as session:
        try:
            item = session.Storage.detail(
                vfolder_host=vfolder_host,
                fields=fields,
            )
            ctx.output.print_item(item, fields)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(1)


@storage.command()
@click.pass_obj
@click.option('--filter', 'filter_', default=None,
              help='Set the query filter expression.')
@click.option('--order', default=None,
              help='Set the query ordering expression.')
@click.option('--offset', default=0,
              help='The index of the current page start for pagination.')
@click.option('--limit', default=None,
              help='The page size for pagination.')
def list(ctx: CLIContext, filter_, order, offset, limit) -> None:
    """
    List storage volumes.
    (super-admin privilege required)
    """
    fields = [
        storage_fields['id'],
        storage_fields['backend'],
        storage_fields['capabilities'],
    ]
    try:
        with Session() as session:
            fetch_func = lambda pg_offset, pg_size: session.Storage.paginated_list(
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
        sys.exit(1)
