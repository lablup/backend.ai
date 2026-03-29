"""User-facing CLI commands for resource allocation."""

from __future__ import annotations

import asyncio
import sys
from typing import Any

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    print_result,
)


def _run_async(coro_fn: Any) -> None:
    """Run an async function with SDK error handling."""
    from ai.backend.client.exceptions import BackendAPIError

    try:
        asyncio.run(coro_fn())
    except BackendAPIError as e:
        data = e.args[2] if len(e.args) > 2 else {}
        title = data.get("title", "") if isinstance(data, dict) else ""
        msg = data.get("msg", "") if isinstance(data, dict) else ""
        status = e.args[0] if e.args else "?"
        detail = title or msg or str(e)
        click.echo(f"Error ({status}): {detail}", err=True)
        sys.exit(1)


@click.group(name="resource-allocation")
def resource_allocation() -> None:
    """Resource allocation commands."""


@resource_allocation.command(name="project-usage")
@click.argument("project_id", type=click.UUID)
def project_usage(project_id: str) -> None:
    """Get resource usage for a project."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_allocation.project_usage(project_id)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@resource_allocation.command(name="resource-group-usage")
@click.argument("rg_name", type=str)
def resource_group_usage(rg_name: str) -> None:
    """Get resource usage for a resource group."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_allocation.resource_group_usage(rg_name)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)
