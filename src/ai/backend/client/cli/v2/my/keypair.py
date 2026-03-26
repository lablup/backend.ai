"""CLI commands for self-service keypair operations."""

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
def keypair() -> None:
    """My keypair commands."""


@keypair.command()
@click.option("--limit", default=None, type=int, help="Maximum number of results to return.")
@click.option("--offset", default=None, type=int, help="Number of results to skip.")
@click.option("--first", default=None, type=int, help="Cursor-based: return first N items.")
@click.option("--after", default=None, type=str, help="Cursor-based: return items after cursor.")
@click.option("--last", default=None, type=int, help="Cursor-based: return last N items.")
@click.option("--before", default=None, type=str, help="Cursor-based: return items before cursor.")
@click.option(
    "--is-active",
    default=None,
    type=bool,
    help="Filter by active state.",
)
@click.option(
    "--access-key-contains",
    default=None,
    type=str,
    help="Filter keypairs whose access key contains this substring.",
)
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., created_at:desc, access_key:asc).",
)
def search(
    limit: int | None,
    offset: int | None,
    first: int | None,
    after: str | None,
    last: int | None,
    before: str | None,
    is_active: bool | None,
    access_key_contains: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search my keypairs."""
    from ai.backend.common.dto.manager.v2.keypair.request import (
        KeypairFilter,
        KeypairOrderBy,
        SearchMyKeypairsRequest,
    )
    from ai.backend.common.dto.manager.v2.keypair.types import KeypairOrderField

    filter_dto: KeypairFilter | None = None
    if any(opt is not None for opt in (is_active, access_key_contains)):
        from ai.backend.common.dto.manager.query import StringFilter

        filter_dto = KeypairFilter(
            is_active=is_active,
            access_key=(
                StringFilter(contains=access_key_contains)
                if access_key_contains is not None
                else None
            ),
        )

    orders = parse_order_options(order_by, KeypairOrderField, KeypairOrderBy) if order_by else None

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            request = SearchMyKeypairsRequest(
                filter=filter_dto,
                order=orders,
                first=first,
                after=after,
                last=last,
                before=before,
                limit=limit,
                offset=offset,
            )
            result = await registry.keypair.search(request)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@keypair.command()
def issue() -> None:
    """Issue a new keypair."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.keypair.issue()
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@keypair.command()
@click.argument("access_key")
def revoke(access_key: str) -> None:
    """Revoke a keypair by access key."""
    from ai.backend.common.dto.manager.v2.keypair.request import RevokeMyKeypairInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.keypair.revoke(
                RevokeMyKeypairInput(access_key=access_key),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@keypair.command()
@click.argument("access_key")
@click.option(
    "--is-active",
    type=bool,
    required=True,
    help="New active state for the keypair.",
)
def update(access_key: str, is_active: bool) -> None:
    """Update a keypair by access key."""
    from ai.backend.common.dto.manager.v2.keypair.request import UpdateMyKeypairInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.keypair.update(
                UpdateMyKeypairInput(access_key=access_key, is_active=is_active),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@keypair.command(name="switch-main")
@click.argument("access_key")
def switch_main(access_key: str) -> None:
    """Switch the main access key."""
    from ai.backend.common.dto.manager.v2.keypair.request import SwitchMyMainAccessKeyInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.keypair.switch_main(
                SwitchMyMainAccessKeyInput(access_key=access_key),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
