"""Admin CLI commands for the session domain."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)


@click.group()
def session() -> None:
    """Admin session commands."""


@session.command(name="search")
@click.option("--limit", type=int, default=20, help="Maximum number of items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
@click.option("--name-contains", type=str, default=None, help="Filter sessions by name (contains).")
@click.option(
    "--status",
    type=str,
    multiple=True,
    help="Filter sessions by status (repeatable, e.g., --status RUNNING --status PENDING).",
)
@click.option(
    "--domain-name", type=str, default=None, help="Filter sessions by domain name (contains)."
)
@click.option(
    "--agent-id",
    type=str,
    default=None,
    help="Scope to sessions running on a specific agent.",
)
@click.option(
    "--order-by",
    multiple=True,
    help=(
        "Order by field:direction (e.g., created_at:desc). "
        "Fields: created_at, terminated_at, status, id, name."
    ),
)
def search(
    limit: int,
    offset: int,
    name_contains: str | None,
    status: tuple[str, ...],
    domain_name: str | None,
    agent_id: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search sessions with admin scope.

    Use --agent-id to scope results to a specific agent.
    """
    from ai.backend.common.dto.manager.query import StringFilter
    from ai.backend.common.dto.manager.v2.session.request import (
        AdminSearchSessionsInput,
        SessionFilter,
        SessionOrder,
    )
    from ai.backend.common.dto.manager.v2.session.types import (
        SessionOrderField,
        SessionStatusEnum,
        SessionStatusFilter,
    )

    # Build filter only if any filter option is provided
    filter_dto: SessionFilter | None = None
    if name_contains is not None or status or domain_name is not None:
        filter_dto = SessionFilter(
            name=StringFilter(contains=name_contains) if name_contains is not None else None,
            status=(
                SessionStatusFilter(in_=[SessionStatusEnum(s) for s in status]) if status else None
            ),
            domain_name=(StringFilter(contains=domain_name) if domain_name is not None else None),
        )

    # Build order only if --order-by is provided
    orders = parse_order_options(order_by, SessionOrderField, SessionOrder) if order_by else None

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            request = AdminSearchSessionsInput(
                filter=filter_dto,
                order=orders,
                limit=limit,
                offset=offset,
            )
            if agent_id is not None:
                result = await registry.session.search_sessions_by_agent(agent_id, request)
            else:
                result = await registry.session.admin_search(request)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


# -- Sub-group: kernel --


@session.group()
def kernel() -> None:
    """Admin session kernel commands."""


@kernel.command(name="search")
@click.option("--limit", type=int, default=20, help="Maximum number of items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
@click.option(
    "--status",
    type=str,
    multiple=True,
    help="Filter kernels by status (repeatable, e.g., --status RUNNING --status TERMINATED).",
)
@click.option(
    "--agent-id",
    type=str,
    default=None,
    help="Scope to kernels running on a specific agent.",
)
@click.option(
    "--session-id",
    type=str,
    default=None,
    help="Scope to kernels belonging to a specific session.",
)
@click.option(
    "--order-by",
    multiple=True,
    help=(
        "Order by field:direction (e.g., created_at:desc). "
        "Fields: cluster_idx, created_at, terminated_at, status."
    ),
)
def kernel_search(
    limit: int,
    offset: int,
    status: tuple[str, ...],
    agent_id: str | None,
    session_id: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search kernels with admin scope.

    Use --agent-id to scope to a specific agent, or --session-id to scope
    to a specific session.
    """
    from ai.backend.common.dto.manager.v2.kernel.request import (
        AdminSearchKernelsInput,
        KernelFilter,
        KernelOrder,
    )
    from ai.backend.common.dto.manager.v2.kernel.types import KernelOrderField, KernelStatusFilter

    # Build filter only if status option is provided
    filter_dto: KernelFilter | None = None
    if status:
        from ai.backend.common.dto.manager.v2.kernel.types import KernelStatusEnum

        filter_dto = KernelFilter(
            status=KernelStatusFilter(
                in_=[KernelStatusEnum(s) for s in status],
            ),
        )

    # Build order only if --order-by is provided
    orders = parse_order_options(order_by, KernelOrderField, KernelOrder) if order_by else None

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            request = AdminSearchKernelsInput(
                filter=filter_dto,
                order=orders,
                limit=limit,
                offset=offset,
            )
            if agent_id is not None:
                result = await registry.session.search_kernels_by_agent(agent_id, request)
            elif session_id is not None:
                result = await registry.session.search_kernels_by_session(session_id, request)
            else:
                result = await registry.session.admin_search_kernels(request)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
