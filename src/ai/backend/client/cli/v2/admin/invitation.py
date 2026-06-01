"""Admin CLI commands for the v2 role invitation resource."""

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
def invitation() -> None:
    """Admin role invitation commands."""


@invitation.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., created_at:desc, state:asc).",
)
def search(limit: int | None, offset: int | None, order_by: tuple[str, ...]) -> None:
    """Search all role invitations across the system (superadmin only)."""
    from ai.backend.common.dto.manager.v2.role_invitation.request import (
        RoleInvitationOrderBy,
        RoleInvitationOrderField,
        SearchRoleInvitationsInput,
    )

    orders = (
        parse_order_options(order_by, RoleInvitationOrderField, RoleInvitationOrderBy)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.role_invitation.admin_search(
                SearchRoleInvitationsInput(order=orders, limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
