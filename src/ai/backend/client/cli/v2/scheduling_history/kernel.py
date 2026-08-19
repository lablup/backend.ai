"""CLI commands for kernel scheduling history."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from uuid import UUID

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)

if TYPE_CHECKING:
    from ai.backend.common.dto.manager.v2.scheduling_history.request import KernelHistoryFilter

# Shared result choices for scheduling history filters
_RESULT_CHOICES = click.Choice(
    ["SUCCESS", "FAILURE", "STALE", "NEED_RETRY", "EXPIRED", "GIVE_UP", "SKIPPED"],
    case_sensitive=False,
)


def _build_kernel_history_filter(
    *,
    phase: str | None,
    from_status: tuple[str, ...],
    to_status: tuple[str, ...],
    result: str | None,
    error_code: str | None,
    message: str | None,
    kernel_id: str | None = None,
    session_id: str | None = None,
) -> KernelHistoryFilter | None:
    """Build a KernelHistoryFilter from explicit CLI options.

    ``kernel_id`` and ``session_id`` are omitted by callers whose scope already
    narrows by that id. Returns None if no filter options were provided.
    """
    from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
    from ai.backend.common.dto.manager.v2.scheduling_history.request import (
        KernelHistoryFilter,
        SchedulingResultFilter,
    )
    from ai.backend.common.dto.manager.v2.scheduling_history.types import SchedulingResultType

    has_any = any(
        opt is not None for opt in (kernel_id, session_id, phase, result, error_code, message)
    )
    if not has_any and not from_status and not to_status:
        return None

    return KernelHistoryFilter(
        kernel_id=UUIDFilter(equals=UUID(kernel_id)) if kernel_id is not None else None,
        session_id=UUIDFilter(equals=UUID(session_id)) if session_id is not None else None,
        phase=StringFilter(contains=phase) if phase is not None else None,
        from_status=list(from_status) if from_status else None,
        to_status=list(to_status) if to_status else None,
        result=(
            SchedulingResultFilter(equals=SchedulingResultType(result))
            if result is not None
            else None
        ),
        error_code=StringFilter(contains=error_code) if error_code is not None else None,
        message=StringFilter(contains=message) if message is not None else None,
    )


@click.group()
def kernel() -> None:
    """Kernel scheduling history commands."""


@kernel.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option("--kernel-id", type=str, default=None, help="Filter by kernel ID (UUID).")
@click.option("--session-id", type=str, default=None, help="Filter by session ID (UUID).")
@click.option("--phase", type=str, default=None, help="Filter by scheduling phase (contains).")
@click.option(
    "--from-status",
    type=str,
    multiple=True,
    help="Filter by from_status values (repeatable).",
)
@click.option(
    "--to-status",
    type=str,
    multiple=True,
    help="Filter by to_status values (repeatable).",
)
@click.option("--result", type=_RESULT_CHOICES, default=None, help="Filter by scheduling result.")
@click.option("--error-code", type=str, default=None, help="Filter by error code (contains).")
@click.option("--message", type=str, default=None, help="Filter by message (contains).")
@click.option(
    "--order-by",
    multiple=True,
    help=(
        "Order by field:direction (e.g., created_at:desc). Fields: created_at, "
        "updated_at, phase, from_status, to_status, result, attempts."
    ),
)
def search(
    limit: int | None,
    offset: int | None,
    kernel_id: str | None,
    session_id: str | None,
    phase: str | None,
    from_status: tuple[str, ...],
    to_status: tuple[str, ...],
    result: str | None,
    error_code: str | None,
    message: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search kernel scheduling histories (superadmin only)."""
    from ai.backend.common.dto.manager.v2.scheduling_history.request import (
        AdminSearchKernelHistoriesInput,
        KernelHistoryOrder,
    )
    from ai.backend.common.dto.manager.v2.scheduling_history.types import KernelHistoryOrderField

    history_filter = _build_kernel_history_filter(
        kernel_id=kernel_id,
        session_id=session_id,
        phase=phase,
        from_status=from_status,
        to_status=to_status,
        result=result,
        error_code=error_code,
        message=message,
    )

    orders = (
        parse_order_options(order_by, KernelHistoryOrderField, KernelHistoryOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result_data = await registry.scheduling_history.search_kernel_history(
                AdminSearchKernelHistoriesInput(
                    filter=history_filter,
                    order=orders,
                    limit=limit,
                    offset=offset,
                ),
            )
            print_result(result_data)
        finally:
            await registry.close()

    asyncio.run(_run())


@kernel.command(name="search-scoped")
@click.argument("kernel_id", type=str)
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option("--session-id", type=str, default=None, help="Filter by session ID (UUID).")
@click.option("--phase", type=str, default=None, help="Filter by scheduling phase (contains).")
@click.option(
    "--from-status",
    type=str,
    multiple=True,
    help="Filter by from_status values (repeatable).",
)
@click.option(
    "--to-status",
    type=str,
    multiple=True,
    help="Filter by to_status values (repeatable).",
)
@click.option("--result", type=_RESULT_CHOICES, default=None, help="Filter by scheduling result.")
@click.option("--error-code", type=str, default=None, help="Filter by error code (contains).")
@click.option("--message", type=str, default=None, help="Filter by message (contains).")
@click.option(
    "--order-by",
    multiple=True,
    help=(
        "Order by field:direction (e.g., created_at:desc). Fields: created_at, "
        "updated_at, phase, from_status, to_status, result, attempts."
    ),
)
def search_scoped(
    kernel_id: str,
    session_id: str | None,
    limit: int | None,
    offset: int | None,
    phase: str | None,
    from_status: tuple[str, ...],
    to_status: tuple[str, ...],
    result: str | None,
    error_code: str | None,
    message: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search kernel scheduling history scoped to KERNEL_ID."""
    from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
    from ai.backend.common.dto.manager.v2.scheduling_history.request import (
        KernelHistoryOrder,
        ScopedSearchKernelHistoriesInput,
    )
    from ai.backend.common.dto.manager.v2.scheduling_history.types import (
        KernelHistoryOrderField,
        KernelHistoryScopeDTO,
    )

    scope = KernelHistoryScopeDTO(kernel=[UUIDScope(value=UUID(kernel_id))])

    # The scope already narrows by kernel ID, so it is not repeated in the filter.
    history_filter = _build_kernel_history_filter(
        session_id=session_id,
        phase=phase,
        from_status=from_status,
        to_status=to_status,
        result=result,
        error_code=error_code,
        message=message,
    )

    orders = (
        parse_order_options(order_by, KernelHistoryOrderField, KernelHistoryOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result_data = await registry.scheduling_history.kernel_scoped_search(
                ScopedSearchKernelHistoriesInput(
                    scope=scope,
                    filter=history_filter,
                    order=orders,
                    limit=limit,
                    offset=offset,
                ),
            )
            print_result(result_data)
        finally:
            await registry.close()

    asyncio.run(_run())
