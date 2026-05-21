"""CLI commands for audit log management."""

from __future__ import annotations

import asyncio
import uuid

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)
from ai.backend.common.dto.manager.v2.rbac.types import (
    EntityTypeScope,
    RBACElementTypeDTO,
    UUIDScope,
)

_TRIGGERED_USER_KEYWORD = "triggered_user"


def _parse_scope_items(
    raw_scopes: tuple[str, ...],
) -> tuple[list[EntityTypeScope], list[UUIDScope]]:
    """Parse ``--scope`` values of form ``<type>:<id>`` into entity / triggered_user buckets."""
    entity: list[EntityTypeScope] = []
    triggered_user: list[UUIDScope] = []
    for raw in raw_scopes:
        if ":" not in raw:
            raise click.BadParameter(
                f"--scope must be in '<type>:<id>' form (got: {raw!r})",
                param_hint="--scope",
            )
        type_part, id_part = raw.split(":", 1)
        type_part = type_part.strip()
        id_part = id_part.strip()
        if not type_part or not id_part:
            raise click.BadParameter(
                f"--scope requires both type and id (got: {raw!r})",
                param_hint="--scope",
            )
        if type_part == _TRIGGERED_USER_KEYWORD:
            try:
                triggered_user.append(UUIDScope(value=uuid.UUID(id_part)))
            except ValueError as exc:
                raise click.BadParameter(
                    f"--scope triggered_user requires a UUID id (got: {id_part!r})",
                    param_hint="--scope",
                ) from exc
            continue
        try:
            element_type = RBACElementTypeDTO(type_part)
        except ValueError as exc:
            valid = ", ".join(sorted(t.value for t in RBACElementTypeDTO))
            raise click.BadParameter(
                f"unknown scope type {type_part!r}; "
                f"expected one of: {_TRIGGERED_USER_KEYWORD}, {valid}",
                param_hint="--scope",
            ) from exc
        entity.append(EntityTypeScope(entity_type=element_type, entity_id=id_part))
    return entity, triggered_user


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


@audit_log.command(name="scoped-search")
@click.option(
    "--scope",
    "scopes",
    multiple=True,
    required=True,
    help=(
        "Scope item in '<type>:<id>' form. "
        f"Use '{_TRIGGERED_USER_KEYWORD}:<user-uuid>' to scope by actor; "
        "otherwise '<entity_type>:<entity_id>' (e.g., 'vfolder:<uuid>', 'project:<uuid>'). "
        "Repeatable; items are OR'd."
    ),
)
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option("--first", type=int, default=None, help="Cursor-forward page size.")
@click.option("--after", type=str, default=None, help="Cursor-forward start cursor.")
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
def scoped_search(
    scopes: tuple[str, ...],
    limit: int | None,
    offset: int | None,
    first: int | None,
    after: str | None,
    entity_type: str | None,
    operation: str | None,
    status: str | None,
    triggered_by: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search audit logs within an RBAC-authorized scope (non-admin)."""
    from ai.backend.common.dto.manager.query import StringFilter
    from ai.backend.common.dto.manager.v2.audit_log.request import (
        AuditLogFilter,
        AuditLogOrder,
        AuditLogScope,
        AuditLogStatusFilter,
        ScopedSearchAuditLogsInput,
    )
    from ai.backend.common.dto.manager.v2.audit_log.types import (
        AuditLogOrderField,
        AuditLogStatus,
    )

    entity_items, triggered_user_items = _parse_scope_items(scopes)
    scope_dto = AuditLogScope(
        entity=entity_items or None,
        triggered_user=triggered_user_items or None,
    )

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

    orders = parse_order_options(order_by, AuditLogOrderField, AuditLogOrder) if order_by else None

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.audit_log.scoped_search(
                ScopedSearchAuditLogsInput(
                    scope=scope_dto,
                    filter=filter_dto,
                    order=orders,
                    limit=limit,
                    offset=offset,
                    first=first,
                    after=after,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
