"""Admin CLI commands for login client types."""

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


@click.group()
def login_client_type() -> None:
    """Login client type admin commands."""


@login_client_type.command()
@click.option("--limit", type=int, default=20, help="Maximum number of items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
@click.option(
    "--name-contains",
    default=None,
    type=str,
    help="Filter by name (substring match).",
)
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., name:asc, created_at:desc).",
)
def search(
    limit: int,
    offset: int,
    name_contains: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search login client types with admin scope."""
    from ai.backend.common.dto.manager.v2.login_client_type.request import (
        LoginClientTypeFilter,
        LoginClientTypeOrder,
        SearchLoginClientTypesInput,
    )
    from ai.backend.common.dto.manager.v2.login_client_type.types import (
        LoginClientTypeOrderField,
    )

    filter_dto: LoginClientTypeFilter | None = None
    if name_contains is not None:
        from ai.backend.common.dto.manager.query import StringFilter

        filter_dto = LoginClientTypeFilter(
            name=StringFilter(contains=name_contains),
        )

    orders = (
        parse_order_options(order_by, LoginClientTypeOrderField, LoginClientTypeOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.login_client_type.search(
                SearchLoginClientTypesInput(
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


@login_client_type.command()
@click.option("--name", required=True, type=str, help="Unique login client type name.")
@click.option("--description", default=None, type=str, help="Optional description.")
def create(name: str, description: str | None) -> None:
    """Create a new login client type (superadmin only)."""
    from ai.backend.common.dto.manager.v2.login_client_type.request import (
        CreateLoginClientTypeInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.login_client_type.admin_create(
                CreateLoginClientTypeInput(name=name, description=description)
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@login_client_type.command()
@click.argument("login_client_type_id", type=click.UUID)
@click.option("--name", default=None, type=str, help="Updated name.")
@click.option("--description", default=None, type=str, help="Updated description.")
def update(
    login_client_type_id: uuid.UUID,
    name: str | None,
    description: str | None,
) -> None:
    """Update a login client type (superadmin only)."""
    from ai.backend.common.dto.manager.v2.login_client_type.request import (
        UpdateLoginClientTypeInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.login_client_type.admin_update(
                login_client_type_id,
                UpdateLoginClientTypeInput(name=name, description=description),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@login_client_type.command()
@click.argument("login_client_type_id", type=click.UUID)
def delete(login_client_type_id: uuid.UUID) -> None:
    """Delete a login client type (superadmin only)."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.login_client_type.admin_delete(login_client_type_id)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
