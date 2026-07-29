"""User-facing CLI commands for idle checker assignments."""

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
    """Idle checker assignment commands."""


def _parse_scope_items(scopes: tuple[str, ...]) -> list[tuple[IdleCheckerScopeTypeDTO, uuid.UUID]]:
    items: list[tuple[IdleCheckerScopeTypeDTO, uuid.UUID]] = []
    for raw in scopes:
        scope_type_raw, sep, scope_id = raw.partition(":")
        if not sep or not scope_id:
            raise click.BadParameter(
                f"Invalid scope item {raw!r}; expected '<scope_type>:<scope_id>'.",
                param_hint="--scope",
            )
        try:
            scope_type = IdleCheckerScopeTypeDTO(scope_type_raw)
        except ValueError:
            valid = ", ".join(member.value for member in IdleCheckerScopeTypeDTO)
            raise click.BadParameter(
                f"Unknown scope type {scope_type_raw!r}; expected one of: {valid}.",
                param_hint="--scope",
            ) from None
        try:
            scope_uuid = uuid.UUID(scope_id)
        except ValueError:
            raise click.BadParameter(
                f"Scope identifier {scope_id!r} must be a UUID.",
                param_hint="--scope",
            ) from None
        items.append((scope_type, scope_uuid))
    return items


@idle_checker_assignment.command(name="scoped-search")
@click.option(
    "--scope",
    "scopes",
    multiple=True,
    required=True,
    help=(
        "Scope item as '<scope_type>:<scope_id>' (repeatable; OR across items). "
        "Example: --scope domain:33db45ef-... --scope project:7b56b1f4-..."
    ),
)
@click.option("--limit", type=int, default=20, help="Maximum number of items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
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
def scoped_search(
    scopes: tuple[str, ...],
    limit: int,
    offset: int,
    enabled: bool | None,
    order_by: tuple[str, ...],
) -> None:
    """Search idle checker assignments within the given scopes (per-item RBAC)."""
    from ai.backend.common.dto.manager.v2.idle_checker_assignment.request import (
        IdleCheckerAssignmentFilter,
        IdleCheckerAssignmentOrder,
        IdleCheckerAssignmentScopeDTO,
        IdleCheckerScopeRefDTO,
        ScopedSearchIdleCheckerAssignmentsInput,
    )
    from ai.backend.common.dto.manager.v2.idle_checker_assignment.types import (
        IdleCheckerAssignmentOrderField,
    )

    scope_refs: list[IdleCheckerScopeRefDTO] = []
    for scope_type, scope_id in _parse_scope_items(scopes):
        scope_refs.append(IdleCheckerScopeRefDTO(scope_type=scope_type, scope_id=scope_id))

    filter_dto = IdleCheckerAssignmentFilter(enabled=enabled) if enabled is not None else None
    orders = (
        parse_order_options(order_by, IdleCheckerAssignmentOrderField, IdleCheckerAssignmentOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.idle_checker_assignment.scoped_search(
                ScopedSearchIdleCheckerAssignmentsInput(
                    scope=IdleCheckerAssignmentScopeDTO(items=scope_refs),
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


@idle_checker_assignment.command()
@click.argument("idle_checker_assignment_id", type=click.UUID)
@click.option(
    "--enabled/--disabled",
    "enabled",
    required=True,
    help="New enabled state.",
)
def update(idle_checker_assignment_id: uuid.UUID, enabled: bool) -> None:
    """Update an idle checker assignment's enabled state by ID."""
    from ai.backend.common.dto.manager.v2.idle_checker_assignment.request import (
        UpdateIdleCheckerAssignmentInput,
    )
    from ai.backend.common.identifier.idle_checker import IdleCheckerAssignmentID

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.idle_checker_assignment.update(
                idle_checker_assignment_id,
                UpdateIdleCheckerAssignmentInput(
                    id=IdleCheckerAssignmentID(idle_checker_assignment_id),
                    enabled=enabled,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@idle_checker_assignment.command()
@click.argument("idle_checker_assignment_id", type=click.UUID)
def purge(idle_checker_assignment_id: uuid.UUID) -> None:
    """Permanently remove an idle checker assignment by ID."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.idle_checker_assignment.purge(idle_checker_assignment_id)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
