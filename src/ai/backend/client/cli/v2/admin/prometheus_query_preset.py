"""Admin CLI commands for the v2 prometheus query definition resource.

Only write operations (create, update, delete) live here. Read operations
(search, get, execute) are user-facing and live under
``cli/v2/prometheus_query_preset/commands.py``.
"""

from __future__ import annotations

import asyncio
from uuid import UUID

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    print_result,
)


@click.group()
def prometheus_query_preset() -> None:
    """Admin prometheus query definition commands."""


@prometheus_query_preset.command()
@click.argument("body", type=str)
def create(body: str) -> None:
    """Create a new prometheus query definition (superadmin only).

    BODY is a JSON string with creation fields.
    """
    import json
    import sys

    from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
        CreateQueryDefinitionInput,
    )

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON: {e}", err=True)
        sys.exit(1)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.prometheus_query_preset.create(
                CreateQueryDefinitionInput(**data),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@prometheus_query_preset.command()
@click.argument("preset_id", type=click.UUID)
@click.argument("body", type=str)
def update(preset_id: UUID, body: str) -> None:
    """Update a prometheus query definition (superadmin only).

    BODY is a JSON string with fields to update.
    """
    import json
    import sys

    from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
        ModifyQueryDefinitionInput,
    )

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON: {e}", err=True)
        sys.exit(1)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.prometheus_query_preset.update(
                preset_id, ModifyQueryDefinitionInput(**data)
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@prometheus_query_preset.command()
@click.argument("preset_id", type=click.UUID)
def delete(preset_id: UUID) -> None:
    """Delete a prometheus query definition (superadmin only)."""
    from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
        DeleteQueryDefinitionInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.prometheus_query_preset.delete(
                DeleteQueryDefinitionInput(id=preset_id),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
