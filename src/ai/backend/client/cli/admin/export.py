"""CLI commands for CSV export operations."""

from __future__ import annotations

import sys
from datetime import datetime
from typing import Optional

import click

from ai.backend.cli.types import ExitCode
from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.types import CLIContext

from . import admin


@admin.group()
def export() -> None:
    """
    CSV export administration commands.

    Supports report-specific exports: users, sessions, projects, audit-logs.
    """


@export.command()
@pass_ctx_obj
def list_reports(ctx: CLIContext) -> None:
    """
    List all available export reports.
    """
    from ai.backend.client.session import Session

    with Session() as session:
        try:
            response = session.Export.list_reports()
            for report in response.reports:
                click.echo(f"\n{report.report_key}: {report.name}")
                click.echo(f"  {report.description}")
                click.echo("  Fields:")
                for field in report.fields:
                    click.echo(f"    - {field.key}: {field.name} ({field.field_type})")
                    if field.description:
                        click.echo(f"        {field.description}")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


# =============================================================================
# Users Export
# =============================================================================


@export.command(name="users")
@pass_ctx_obj
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    default=None,
    help="Output file path. If not specified, outputs to stdout.",
)
@click.option(
    "--fields",
    type=str,
    default=None,
    help="Comma-separated field keys to include (default: all fields).",
)
@click.option("--filter-username", type=str, default=None, help="Filter by username (contains).")
@click.option("--filter-email", type=str, default=None, help="Filter by email (contains).")
@click.option("--filter-domain", type=str, default=None, help="Filter by domain name (contains).")
@click.option("--filter-role", type=str, default=None, help="Filter by role (equals).")
@click.option("--filter-status", type=str, default=None, help="Filter by status (equals).")
@click.option(
    "--filter-after",
    type=click.DateTime(),
    default=None,
    help="Filter by created_at after this datetime.",
)
@click.option(
    "--filter-before",
    type=click.DateTime(),
    default=None,
    help="Filter by created_at before this datetime.",
)
@click.option(
    "--order",
    "-O",
    "orders",
    type=str,
    multiple=True,
    help="Order by field (format: 'field:asc' or 'field:desc').",
)
@click.option("--encoding", type=str, default="utf-8", help="CSV encoding (default: utf-8).")
def export_users(
    ctx: CLIContext,
    output: Optional[str],
    fields: Optional[str],
    filter_username: Optional[str],
    filter_email: Optional[str],
    filter_domain: Optional[str],
    filter_role: Optional[str],
    filter_status: Optional[str],
    filter_after: Optional[datetime],
    filter_before: Optional[datetime],
    orders: tuple[str, ...],
    encoding: str,
) -> None:
    """
    Export users as CSV.
    """
    from ai.backend.client.session import Session
    from ai.backend.common.dto.manager.export import (
        OrderDirection,
        UserExportFilter,
        UserExportOrder,
        UserExportOrderField,
    )
    from ai.backend.common.dto.manager.query import DateTimeRangeFilter, StringFilter

    field_list = [f.strip() for f in fields.split(",")] if fields else None

    # Build filter
    user_filter: Optional[UserExportFilter] = None
    if any([
        filter_username,
        filter_email,
        filter_domain,
        filter_role,
        filter_status,
        filter_after,
        filter_before,
    ]):
        user_filter = UserExportFilter(
            username=StringFilter(contains=filter_username) if filter_username else None,
            email=StringFilter(contains=filter_email) if filter_email else None,
            domain_name=StringFilter(contains=filter_domain) if filter_domain else None,
            role=[filter_role] if filter_role else None,
            status=[filter_status] if filter_status else None,
            created_at=DateTimeRangeFilter(after=filter_after, before=filter_before)
            if filter_after or filter_before
            else None,
        )

    # Build orders
    user_orders: Optional[list[UserExportOrder]] = None
    if orders:
        user_orders = []
        for order_spec in orders:
            if ":" in order_spec:
                field, direction = order_spec.rsplit(":", 1)
                direction = direction.lower()
            else:
                field = order_spec
                direction = "asc"
            if direction not in ("asc", "desc"):
                click.echo(f"Invalid order direction: {direction}", err=True)
                sys.exit(ExitCode.FAILURE)
            user_orders.append(
                UserExportOrder(
                    field=UserExportOrderField(field), direction=OrderDirection(direction)
                )
            )

    with Session() as session:
        try:
            if output:
                with open(output, "wb") as f:
                    f.writelines(
                        session.Export.stream_users_csv(
                            fields=field_list,
                            filter=user_filter,
                            order=user_orders,
                            encoding=encoding,
                        )
                    )
                click.echo(f"Exported to {output}")
            else:
                for chunk in session.Export.stream_users_csv(
                    fields=field_list, filter=user_filter, order=user_orders, encoding=encoding
                ):
                    sys.stdout.buffer.write(chunk)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


# =============================================================================
# Sessions Export
# =============================================================================


@export.command(name="sessions")
@pass_ctx_obj
@click.option("-o", "--output", type=click.Path(), default=None, help="Output file path.")
@click.option("--fields", type=str, default=None, help="Comma-separated field keys.")
@click.option("--filter-name", type=str, default=None, help="Filter by session name (contains).")
@click.option("--filter-type", type=str, default=None, help="Filter by session type (equals).")
@click.option("--filter-domain", type=str, default=None, help="Filter by domain name (contains).")
@click.option(
    "--filter-access-key", type=str, default=None, help="Filter by access key (contains)."
)
@click.option("--filter-status", type=str, default=None, help="Filter by status (equals).")
@click.option(
    "--filter-scaling-group", type=str, default=None, help="Filter by scaling group (contains)."
)
@click.option(
    "--filter-created-after", type=click.DateTime(), default=None, help="Filter created_at after."
)
@click.option(
    "--filter-created-before", type=click.DateTime(), default=None, help="Filter created_at before."
)
@click.option(
    "--filter-terminated-after",
    type=click.DateTime(),
    default=None,
    help="Filter terminated_at after.",
)
@click.option(
    "--filter-terminated-before",
    type=click.DateTime(),
    default=None,
    help="Filter terminated_at before.",
)
@click.option(
    "--order", "-O", "orders", type=str, multiple=True, help="Order by field (format: 'field:asc')."
)
@click.option("--encoding", type=str, default="utf-8", help="CSV encoding.")
def export_sessions(
    ctx: CLIContext,
    output: Optional[str],
    fields: Optional[str],
    filter_name: Optional[str],
    filter_type: Optional[str],
    filter_domain: Optional[str],
    filter_access_key: Optional[str],
    filter_status: Optional[str],
    filter_scaling_group: Optional[str],
    filter_created_after: Optional[datetime],
    filter_created_before: Optional[datetime],
    filter_terminated_after: Optional[datetime],
    filter_terminated_before: Optional[datetime],
    orders: tuple[str, ...],
    encoding: str,
) -> None:
    """
    Export sessions as CSV.
    """
    from ai.backend.client.session import Session
    from ai.backend.common.dto.manager.export import (
        OrderDirection,
        SessionExportFilter,
        SessionExportOrder,
        SessionExportOrderField,
    )
    from ai.backend.common.dto.manager.query import DateTimeRangeFilter, StringFilter

    field_list = [f.strip() for f in fields.split(",")] if fields else None

    # Build filter
    session_filter: Optional[SessionExportFilter] = None
    if any([
        filter_name,
        filter_type,
        filter_domain,
        filter_access_key,
        filter_status,
        filter_scaling_group,
        filter_created_after,
        filter_created_before,
        filter_terminated_after,
        filter_terminated_before,
    ]):
        session_filter = SessionExportFilter(
            name=StringFilter(contains=filter_name) if filter_name else None,
            session_type=[filter_type] if filter_type else None,
            domain_name=StringFilter(contains=filter_domain) if filter_domain else None,
            access_key=StringFilter(contains=filter_access_key) if filter_access_key else None,
            status=[filter_status] if filter_status else None,
            scaling_group_name=StringFilter(contains=filter_scaling_group)
            if filter_scaling_group
            else None,
            created_at=DateTimeRangeFilter(after=filter_created_after, before=filter_created_before)
            if filter_created_after or filter_created_before
            else None,
            terminated_at=DateTimeRangeFilter(
                after=filter_terminated_after, before=filter_terminated_before
            )
            if filter_terminated_after or filter_terminated_before
            else None,
        )

    # Build orders
    session_orders: Optional[list[SessionExportOrder]] = None
    if orders:
        session_orders = []
        for order_spec in orders:
            if ":" in order_spec:
                field, direction = order_spec.rsplit(":", 1)
                direction = direction.lower()
            else:
                field = order_spec
                direction = "asc"
            if direction not in ("asc", "desc"):
                click.echo(f"Invalid order direction: {direction}", err=True)
                sys.exit(ExitCode.FAILURE)
            session_orders.append(
                SessionExportOrder(
                    field=SessionExportOrderField(field), direction=OrderDirection(direction)
                )
            )

    with Session() as session:
        try:
            if output:
                with open(output, "wb") as f:
                    f.writelines(
                        session.Export.stream_sessions_csv(
                            fields=field_list,
                            filter=session_filter,
                            order=session_orders,
                            encoding=encoding,
                        )
                    )
                click.echo(f"Exported to {output}")
            else:
                for chunk in session.Export.stream_sessions_csv(
                    fields=field_list,
                    filter=session_filter,
                    order=session_orders,
                    encoding=encoding,
                ):
                    sys.stdout.buffer.write(chunk)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


# =============================================================================
# Projects Export
# =============================================================================


@export.command(name="projects")
@pass_ctx_obj
@click.option("-o", "--output", type=click.Path(), default=None, help="Output file path.")
@click.option("--fields", type=str, default=None, help="Comma-separated field keys.")
@click.option("--filter-name", type=str, default=None, help="Filter by project name (contains).")
@click.option("--filter-domain", type=str, default=None, help="Filter by domain name (contains).")
@click.option(
    "--filter-active/--filter-inactive",
    default=None,
    help="Filter by active status (--filter-active or --filter-inactive).",
)
@click.option(
    "--filter-after", type=click.DateTime(), default=None, help="Filter created_at after."
)
@click.option(
    "--filter-before", type=click.DateTime(), default=None, help="Filter created_at before."
)
@click.option(
    "--order", "-O", "orders", type=str, multiple=True, help="Order by field (format: 'field:asc')."
)
@click.option("--encoding", type=str, default="utf-8", help="CSV encoding.")
def export_projects(
    ctx: CLIContext,
    output: Optional[str],
    fields: Optional[str],
    filter_name: Optional[str],
    filter_domain: Optional[str],
    filter_active: Optional[bool],
    filter_after: Optional[datetime],
    filter_before: Optional[datetime],
    orders: tuple[str, ...],
    encoding: str,
) -> None:
    """
    Export projects as CSV.
    """
    from ai.backend.client.session import Session
    from ai.backend.common.dto.manager.export import (
        BooleanFilter,
        OrderDirection,
        ProjectExportFilter,
        ProjectExportOrder,
        ProjectExportOrderField,
    )
    from ai.backend.common.dto.manager.query import DateTimeRangeFilter, StringFilter

    field_list = [f.strip() for f in fields.split(",")] if fields else None

    # Build filter
    project_filter: Optional[ProjectExportFilter] = None
    if any([filter_name, filter_domain, filter_active is not None, filter_after, filter_before]):
        project_filter = ProjectExportFilter(
            name=StringFilter(contains=filter_name) if filter_name else None,
            domain_name=StringFilter(contains=filter_domain) if filter_domain else None,
            is_active=BooleanFilter(equals=filter_active) if filter_active is not None else None,
            created_at=DateTimeRangeFilter(after=filter_after, before=filter_before)
            if filter_after or filter_before
            else None,
        )

    # Build orders
    project_orders: Optional[list[ProjectExportOrder]] = None
    if orders:
        project_orders = []
        for order_spec in orders:
            if ":" in order_spec:
                field, direction = order_spec.rsplit(":", 1)
                direction = direction.lower()
            else:
                field = order_spec
                direction = "asc"
            if direction not in ("asc", "desc"):
                click.echo(f"Invalid order direction: {direction}", err=True)
                sys.exit(ExitCode.FAILURE)
            project_orders.append(
                ProjectExportOrder(
                    field=ProjectExportOrderField(field), direction=OrderDirection(direction)
                )
            )

    with Session() as session:
        try:
            if output:
                with open(output, "wb") as f:
                    f.writelines(
                        session.Export.stream_projects_csv(
                            fields=field_list,
                            filter=project_filter,
                            order=project_orders,
                            encoding=encoding,
                        )
                    )
                click.echo(f"Exported to {output}")
            else:
                for chunk in session.Export.stream_projects_csv(
                    fields=field_list,
                    filter=project_filter,
                    order=project_orders,
                    encoding=encoding,
                ):
                    sys.stdout.buffer.write(chunk)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


# =============================================================================
# Audit Logs Export
# =============================================================================


@export.command(name="audit-logs")
@pass_ctx_obj
@click.option("-o", "--output", type=click.Path(), default=None, help="Output file path.")
@click.option("--fields", type=str, default=None, help="Comma-separated field keys.")
@click.option(
    "--filter-entity-type", type=str, default=None, help="Filter by entity type (equals)."
)
@click.option("--filter-entity-id", type=str, default=None, help="Filter by entity ID (contains).")
@click.option("--filter-operation", type=str, default=None, help="Filter by operation (equals).")
@click.option("--filter-status", type=str, default=None, help="Filter by status (equals).")
@click.option(
    "--filter-triggered-by", type=str, default=None, help="Filter by triggered_by (contains)."
)
@click.option(
    "--filter-request-id", type=str, default=None, help="Filter by request ID (contains)."
)
@click.option(
    "--filter-after", type=click.DateTime(), default=None, help="Filter created_at after."
)
@click.option(
    "--filter-before", type=click.DateTime(), default=None, help="Filter created_at before."
)
@click.option(
    "--order", "-O", "orders", type=str, multiple=True, help="Order by field (format: 'field:asc')."
)
@click.option("--encoding", type=str, default="utf-8", help="CSV encoding.")
def export_audit_logs(
    ctx: CLIContext,
    output: Optional[str],
    fields: Optional[str],
    filter_entity_type: Optional[str],
    filter_entity_id: Optional[str],
    filter_operation: Optional[str],
    filter_status: Optional[str],
    filter_triggered_by: Optional[str],
    filter_request_id: Optional[str],
    filter_after: Optional[datetime],
    filter_before: Optional[datetime],
    orders: tuple[str, ...],
    encoding: str,
) -> None:
    """
    Export audit logs as CSV.
    """
    from ai.backend.client.session import Session
    from ai.backend.common.dto.manager.export import (
        AuditLogExportFilter,
        AuditLogExportOrder,
        AuditLogExportOrderField,
        OrderDirection,
    )
    from ai.backend.common.dto.manager.query import DateTimeRangeFilter, StringFilter

    field_list = [f.strip() for f in fields.split(",")] if fields else None

    # Build filter
    audit_log_filter: Optional[AuditLogExportFilter] = None
    if any([
        filter_entity_type,
        filter_entity_id,
        filter_operation,
        filter_status,
        filter_triggered_by,
        filter_request_id,
        filter_after,
        filter_before,
    ]):
        audit_log_filter = AuditLogExportFilter(
            entity_type=StringFilter(equals=filter_entity_type) if filter_entity_type else None,
            entity_id=StringFilter(contains=filter_entity_id) if filter_entity_id else None,
            operation=StringFilter(equals=filter_operation) if filter_operation else None,
            status=[filter_status] if filter_status else None,
            triggered_by=StringFilter(contains=filter_triggered_by)
            if filter_triggered_by
            else None,
            request_id=StringFilter(contains=filter_request_id) if filter_request_id else None,
            created_at=DateTimeRangeFilter(after=filter_after, before=filter_before)
            if filter_after or filter_before
            else None,
        )

    # Build orders
    audit_log_orders: Optional[list[AuditLogExportOrder]] = None
    if orders:
        audit_log_orders = []
        for order_spec in orders:
            if ":" in order_spec:
                field, direction = order_spec.rsplit(":", 1)
                direction = direction.lower()
            else:
                field = order_spec
                direction = "asc"
            if direction not in ("asc", "desc"):
                click.echo(f"Invalid order direction: {direction}", err=True)
                sys.exit(ExitCode.FAILURE)
            audit_log_orders.append(
                AuditLogExportOrder(
                    field=AuditLogExportOrderField(field), direction=OrderDirection(direction)
                )
            )

    with Session() as session:
        try:
            if output:
                with open(output, "wb") as f:
                    f.writelines(
                        session.Export.stream_audit_logs_csv(
                            fields=field_list,
                            filter=audit_log_filter,
                            order=audit_log_orders,
                            encoding=encoding,
                        )
                    )
                click.echo(f"Exported to {output}")
            else:
                for chunk in session.Export.stream_audit_logs_csv(
                    fields=field_list,
                    filter=audit_log_filter,
                    order=audit_log_orders,
                    encoding=encoding,
                ):
                    sys.stdout.buffer.write(chunk)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)
