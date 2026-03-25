"""CLI commands for notification channel management."""

from __future__ import annotations

import asyncio
from uuid import UUID

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)


@click.group()
def channel() -> None:
    """Notification channel commands."""


@channel.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option(
    "--name-contains",
    default=None,
    type=str,
    help="Filter channels whose name contains this substring.",
)
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., name:asc, created_at:desc).",
)
def search(
    limit: int | None,
    offset: int | None,
    name_contains: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search notification channels."""
    from ai.backend.common.dto.manager.v2.notification.request import (
        NotificationChannelFilter,
        NotificationChannelOrder,
        SearchNotificationChannelsInput,
    )
    from ai.backend.common.dto.manager.v2.notification.types import NotificationChannelOrderField

    # Build filter only if any filter option is provided
    filter_dto: NotificationChannelFilter | None = None
    if name_contains is not None:
        from ai.backend.common.dto.manager.query import StringFilter

        filter_dto = NotificationChannelFilter(
            name=StringFilter(contains=name_contains),
        )

    # Build order only if --order-by is provided
    orders = (
        parse_order_options(order_by, NotificationChannelOrderField, NotificationChannelOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.notification.search_channels(
                SearchNotificationChannelsInput(
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


@channel.command()
@click.argument("channel_id", type=str)
def get(channel_id: str) -> None:
    """Get a notification channel by ID."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.notification.get_channel(UUID(channel_id))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@channel.command()
@click.argument("channel_id", type=str)
def delete(channel_id: str) -> None:
    """Delete a notification channel."""
    from ai.backend.common.dto.manager.v2.notification.request import (
        DeleteNotificationChannelInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.notification.delete_channel(
                DeleteNotificationChannelInput(id=UUID(channel_id)),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
