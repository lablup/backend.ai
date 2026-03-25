"""CLI commands for audit log management."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)


@click.group(name="audit-log")
def audit_log() -> None:
    """Audit log commands."""


@audit_log.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option(
    "--entity-type",
    type=str,
    default=None,
    help="Filter by entity type (contains).",
)
@click.option(
    "--operation",
    type=str,
    default=None,
    help="Filter by operation (contains).",
)
@click.option(
    "--status",
    type=click.Choice(["success", "error", "unknown", "running"], case_sensitive=False),
    default=None,
    help="Filter by audit log status.",
)
@click.option(
    "--triggered-by",
    type=str,
    default=None,
    help="Filter by triggered-by user (contains).",
)
@click.option(
    "--order-by",
    multiple=True,
    help=(
        "Order by field:direction (e.g., created_at:desc). "
        "Fields: created_at, entity_type, operation, status."
    ),
)
def search(
    limit: int | None,
    offset: int | None,
    entity_type: str | None,
    operation: str | None,
    status: str | None,
    triggered_by: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search audit logs."""
    from ai.backend.common.dto.manager.query import StringFilter
    from ai.backend.common.dto.manager.v2.audit_log.request import (
        AdminSearchAuditLogsInput,
        AuditLogFilter,
        AuditLogOrder,
        AuditLogStatusFilter,
    )
    from ai.backend.common.dto.manager.v2.audit_log.types import (
        AuditLogOrderField,
        AuditLogStatus,
    )

    # Build filter only if any filter option is provided
    filter_dto: AuditLogFilter | None = None
    if any(opt is not None for opt in (entity_type, operation, status, triggered_by)):
        filter_dto = AuditLogFilter(
            entity_type=(StringFilter(contains=entity_type) if entity_type is not None else None),
            operation=StringFilter(contains=operation) if operation is not None else None,
            status=(
                AuditLogStatusFilter(equals=AuditLogStatus(status)) if status is not None else None
            ),
            triggered_by=(
                StringFilter(contains=triggered_by) if triggered_by is not None else None
            ),
        )

    # Build order only if --order-by is provided
    orders = parse_order_options(order_by, AuditLogOrderField, AuditLogOrder) if order_by else None

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.audit_log.search(
                AdminSearchAuditLogsInput(
                    filter=filter_dto,
                    order=orders,
                    limit=limit,
                    offset=offset,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
