"""Admin CLI commands for the v2 agent resource."""

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
def agent() -> None:
    """Admin agent commands."""


@agent.command()
@click.option("--limit", default=20, help="Maximum number of results to return.")
@click.option("--offset", default=0, help="Number of results to skip.")
@click.option(
    "--status",
    default=None,
    type=click.Choice(["ALIVE", "LOST", "RESTARTING", "TERMINATED"], case_sensitive=False),
    help="Filter by agent status.",
)
@click.option(
    "--scaling-group",
    default=None,
    type=str,
    help="Filter agents whose scaling group contains this substring.",
)
@click.option(
    "--schedulable/--no-schedulable",
    default=None,
    help="Filter by schedulable flag.",
)
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., status:asc, first_contact:desc).",
)
def search(
    limit: int,
    offset: int,
    status: str | None,
    scaling_group: str | None,
    schedulable: bool | None,
    order_by: tuple[str, ...],
) -> None:
    """Search agents (superadmin only)."""
    from ai.backend.common.dto.manager.v2.agent.request import (
        AdminSearchAgentsInput,
        AgentFilter,
        AgentOrder,
    )
    from ai.backend.common.dto.manager.v2.agent.types import AgentOrderField

    # Build filter only if any filter option is provided
    filter_dto: AgentFilter | None = None
    if any(opt is not None for opt in (status, scaling_group, schedulable)):
        from ai.backend.common.dto.manager.query import StringFilter
        from ai.backend.common.dto.manager.v2.agent.types import AgentStatusEnum, AgentStatusFilter

        filter_dto = AgentFilter(
            status=(
                AgentStatusFilter(equals=AgentStatusEnum(status.upper()))
                if status is not None
                else None
            ),
            scaling_group=(
                StringFilter(contains=scaling_group) if scaling_group is not None else None
            ),
            schedulable=schedulable,
        )

    # Build order only if --order-by is provided
    orders = parse_order_options(order_by, AgentOrderField, AgentOrder) if order_by else None

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.agent.admin_search(
                AdminSearchAgentsInput(
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


@agent.command(name="total-resources")
def total_resources() -> None:
    """Get aggregate resource statistics across all agents (superadmin only)."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.agent.get_total_resources()
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
