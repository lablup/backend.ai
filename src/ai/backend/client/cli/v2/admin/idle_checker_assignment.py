"""Admin CLI commands for idle checker assignments."""

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
from ai.backend.common.dto.manager.v2.idle_checker_assignment.types import IdleCheckerScopeTypeDTO


@click.group()
def idle_checker_assignment() -> None:
    """Idle checker assignment admin commands (superadmin required)."""


@idle_checker_assignment.command()
@click.option(
    "--scope-type",
    required=True,
    type=click.Choice([scope_type.value for scope_type in IdleCheckerScopeTypeDTO]),
    help="Kind of the scope to bind.",
)
@click.option(
    "--scope-id",
    required=True,
    type=str,
    help="Scope identifier (UUID), interpreted according to the scope type.",
)
@click.option("--idle-checker-id", required=True, type=click.UUID, help="Idle checker to bind.")
@click.option(
    "--enabled/--disabled",
    default=True,
    help="Whether the assignment participates in idle checking (default: enabled).",
)
def create(scope_type: str, scope_id: str, idle_checker_id: uuid.UUID, enabled: bool) -> None:
    """Bind a global idle checker to a scope."""
    from ai.backend.common.dto.manager.v2.idle_checker_assignment.request import (
        CreateIdleCheckerAssignmentInput,
        IdleCheckerScopeRefDTO,
    )
    from ai.backend.common.identifier.idle_checker import IdleCheckerID

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.idle_checker_assignment.admin_create(
                CreateIdleCheckerAssignmentInput(
                    scope=IdleCheckerScopeRefDTO(
                        scope_type=IdleCheckerScopeTypeDTO(scope_type),
                        scope_id=scope_id,
                    ),
                    idle_checker_id=IdleCheckerID(idle_checker_id),
                    enabled=enabled,
                )
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@idle_checker_assignment.command()
@click.option("--limit", type=int, default=20, help="Maximum number of items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
@click.option(
    "--scope-type",
    default=None,
    type=click.Choice([scope_type.value for scope_type in IdleCheckerScopeTypeDTO]),
    help="Filter by scope type (exact match).",
)
@click.option(
    "--idle-checker-id",
    default=None,
    type=click.UUID,
    help="Filter by bound idle checker ID (exact match).",
)
@click.option(
    "--enabled/--disabled",
    "enabled",
    default=None,
    help="Filter by the enabled flag.",
)
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., created_at:desc, scope_type:asc).",
)
def search(
    limit: int,
    offset: int,
    scope_type: str | None,
    idle_checker_id: uuid.UUID | None,
    enabled: bool | None,
    order_by: tuple[str, ...],
) -> None:
    """Search idle checker assignments across all scopes."""
    from ai.backend.common.dto.manager.query import UUIDFilter
    from ai.backend.common.dto.manager.v2.idle_checker_assignment.request import (
        IdleCheckerAssignmentFilter,
        IdleCheckerAssignmentOrder,
        SearchIdleCheckerAssignmentsInput,
    )
    from ai.backend.common.dto.manager.v2.idle_checker_assignment.types import (
        IdleCheckerAssignmentOrderField,
        ScopeTypeFilter,
    )

    filter_dto: IdleCheckerAssignmentFilter | None = None
    if scope_type is not None or idle_checker_id is not None or enabled is not None:
        filter_dto = IdleCheckerAssignmentFilter(
            scope_type=(
                ScopeTypeFilter(equals=IdleCheckerScopeTypeDTO(scope_type))
                if scope_type is not None
                else None
            ),
            idle_checker_id=(
                UUIDFilter(equals=idle_checker_id) if idle_checker_id is not None else None
            ),
            enabled=enabled,
        )

    orders = (
        parse_order_options(order_by, IdleCheckerAssignmentOrderField, IdleCheckerAssignmentOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.idle_checker_assignment.admin_search(
                SearchIdleCheckerAssignmentsInput(
                    filter=filter_dto,
                    order=orders,
                    limit=limit,
                    offset=offset,
                )
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
