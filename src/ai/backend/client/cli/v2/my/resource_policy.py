"""Self-service CLI commands for resource policy."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    print_result,
)


@click.group()
def resource_policy() -> None:
    """My resource policy commands."""


@resource_policy.command(name="keypair")
def my_keypair_resource_policy() -> None:
    """Show my keypair resource policy."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_policy.get_my_keypair_resource_policy()
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@resource_policy.command(name="user")
def my_user_resource_policy() -> None:
    """Show my user resource policy."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_policy.get_my_user_resource_policy()
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
