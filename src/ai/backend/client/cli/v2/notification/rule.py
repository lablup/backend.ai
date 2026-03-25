"""CLI commands for notification rule management."""

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
def rule() -> None:
    """Notification rule commands."""


@rule.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option(
    "--name-contains",
    default=None,
    type=str,
    help="Filter rules whose name contains this substring.",
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
    """Search notification rules."""
    from ai.backend.common.dto.manager.v2.notification.request import (
        NotificationRuleFilter,
        NotificationRuleOrder,
        SearchNotificationRulesInput,
    )
    from ai.backend.common.dto.manager.v2.notification.types import NotificationRuleOrderField

    # Build filter only if any filter option is provided
    filter_dto: NotificationRuleFilter | None = None
    if name_contains is not None:
        from ai.backend.common.dto.manager.query import StringFilter

        filter_dto = NotificationRuleFilter(
            name=StringFilter(contains=name_contains),
        )

    # Build order only if --order-by is provided
    orders = (
        parse_order_options(order_by, NotificationRuleOrderField, NotificationRuleOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.notification.search_rules(
                SearchNotificationRulesInput(
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


@rule.command()
@click.argument("rule_id", type=str)
def get(rule_id: str) -> None:
    """Get a notification rule by ID."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.notification.get_rule(UUID(rule_id))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@rule.command()
@click.argument("rule_id", type=str)
def delete(rule_id: str) -> None:
    """Delete a notification rule."""
    from ai.backend.common.dto.manager.v2.notification.request import (
        DeleteNotificationRuleInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.notification.delete_rule(
                DeleteNotificationRuleInput(id=UUID(rule_id)),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
