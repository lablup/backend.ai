"""CLI commands for notification management."""

from __future__ import annotations

import asyncio
from uuid import UUID

import click

from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.types import CLIContext
from ai.backend.client.cli.v2.helpers import create_v2_registry, print_result


@click.group()
def notifications() -> None:
    """Notification management commands."""


# ------------------------------------------------------------------ Channels


@notifications.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@pass_ctx_obj
def search_channels(ctx: CLIContext, limit: int | None, offset: int | None) -> None:
    """Search notification channels."""
    from ai.backend.common.dto.manager.v2.notification.request import (
        SearchNotificationChannelsInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.notification.search_channels(
                SearchNotificationChannelsInput(limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@notifications.command()
@click.argument("channel_id", type=str)
@pass_ctx_obj
def get_channel(ctx: CLIContext, channel_id: str) -> None:
    """Get a notification channel by ID."""

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.notification.get_channel(UUID(channel_id))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@notifications.command()
@click.argument("channel_id", type=str)
@pass_ctx_obj
def delete_channel(ctx: CLIContext, channel_id: str) -> None:
    """Delete a notification channel."""
    from ai.backend.common.dto.manager.v2.notification.request import (
        DeleteNotificationChannelInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.notification.delete_channel(
                DeleteNotificationChannelInput(id=UUID(channel_id)),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


# ------------------------------------------------------------------ Rules


@notifications.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@pass_ctx_obj
def search_rules(ctx: CLIContext, limit: int | None, offset: int | None) -> None:
    """Search notification rules."""
    from ai.backend.common.dto.manager.v2.notification.request import (
        SearchNotificationRulesInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.notification.search_rules(
                SearchNotificationRulesInput(limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@notifications.command()
@click.argument("rule_id", type=str)
@pass_ctx_obj
def get_rule(ctx: CLIContext, rule_id: str) -> None:
    """Get a notification rule by ID."""

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.notification.get_rule(UUID(rule_id))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@notifications.command()
@click.argument("rule_id", type=str)
@pass_ctx_obj
def delete_rule(ctx: CLIContext, rule_id: str) -> None:
    """Delete a notification rule."""
    from ai.backend.common.dto.manager.v2.notification.request import (
        DeleteNotificationRuleInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.notification.delete_rule(
                DeleteNotificationRuleInput(id=UUID(rule_id)),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
