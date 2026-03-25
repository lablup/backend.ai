"""CLI commands for resource group management."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.types import CLIContext
from ai.backend.client.cli.v2._helpers import create_v2_registry, print_result


@click.group()
def resource_groups() -> None:
    """Resource group management commands."""


@resource_groups.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@pass_ctx_obj
def search(ctx: CLIContext, limit: int | None, offset: int | None) -> None:
    """Search resource groups."""
    from ai.backend.common.dto.manager.v2.resource_group.request import (
        AdminSearchResourceGroupsInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.resource_group.search(
                AdminSearchResourceGroupsInput(limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@resource_groups.command()
@click.argument("name", type=str)
@pass_ctx_obj
def get(ctx: CLIContext, name: str) -> None:
    """Get a resource group by name."""

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.resource_group.get(name)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@resource_groups.command()
@click.option("--name", required=True, help="Resource group name.")
@click.option("--domain-name", required=True, help="Domain name.")
@click.option("--description", default=None, help="Description.")
@pass_ctx_obj
def create(ctx: CLIContext, name: str, domain_name: str, description: str | None) -> None:
    """Create a new resource group."""
    from ai.backend.common.dto.manager.v2.resource_group.request import CreateResourceGroupInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.resource_group.create(
                CreateResourceGroupInput(
                    name=name,
                    domain_name=domain_name,
                    description=description,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@resource_groups.command()
@click.argument("name", type=str)
@pass_ctx_obj
def delete(ctx: CLIContext, name: str) -> None:
    """Delete a resource group by name."""

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.resource_group.delete(name)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@resource_groups.command()
@click.argument("name", type=str)
@pass_ctx_obj
def resource_info(ctx: CLIContext, name: str) -> None:
    """Get resource information for a resource group."""

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.resource_group.get_resource_info(name)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
