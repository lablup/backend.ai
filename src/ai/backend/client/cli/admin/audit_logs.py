from __future__ import annotations

import sys

import click

from ai.backend.client.output.fields import auditlog_fields
from ai.backend.client.session import Session

from ..extensions import pass_ctx_obj
from ..types import CLIContext
from . import admin


@admin.group()
def audit_logs() -> None:
    """
    Events audit logs commands.
    """


@audit_logs.command()
# @click.pass_obj
@pass_ctx_obj
@click.option("-u", "--user-id", type=str, default=None, help="User ID to audit.")
@click.option("--filter", "filter_", default=None, help="Set the query filter expression.")
@click.option("--order", default=None, help="Set the query ordering expression.")
@click.option("--offset", default=0, help="The index of the current page start for pagination.")
@click.option("--limit", default=None, help="The page size for pagination.")
def list(ctx: CLIContext, user_id, filter_, order, offset, limit) -> None:
    """
    List audit logs.
    (admin privilege required)
    """
    fields = [
        auditlog_fields["user_id"],
        auditlog_fields["access_key"],
        auditlog_fields["email"],
        auditlog_fields["action"],
        auditlog_fields["target_type"],
        auditlog_fields["target"],
        auditlog_fields["data"],
        auditlog_fields["created_at"],
    ]
    try:
        with Session() as session:
            fetch_func = lambda pg_offset, pg_size: session.AuditLog.paginated_list(
                user_id,
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
