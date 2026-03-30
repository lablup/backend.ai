"""Self-service CLI commands for resource allocation."""

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
    """My resource allocation commands."""


@resource_allocation.command(name="keypair-usage")
def keypair_usage() -> None:
    """Show my keypair resource usage."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_allocation.my_keypair_usage()
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)


@resource_allocation.command(name="effective")
@click.option("--project-id", required=True, type=click.UUID, help="Project ID.")
@click.option("--resource-group", required=True, type=str, help="Resource group name.")
def effective(project_id: str, resource_group: str) -> None:
    """Show effective resource allocation for the current user."""
    from ai.backend.common.dto.manager.v2.resource_allocation.request import (
        EffectiveResourceAllocationInput,
    )

    request = EffectiveResourceAllocationInput(
        project_id=project_id,
        resource_group_name=resource_group,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_allocation.effective(request)
            print_result(result)
        finally:
            await registry.close()

    _run_async(_run)
