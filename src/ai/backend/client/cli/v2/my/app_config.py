"""Self-service CLI commands for the merged AppConfig view."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, cast

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    print_result,
)


@click.group(name="app-config")
def app_config() -> None:
    """Self-service AppConfig commands for the current user.

    Self-service search has moved to the scoped surface — use
    `bai app-config search --user-id <your-id>`.
    """


def _load_items(items_arg: str) -> list[dict[str, Any]]:
    """Accept JSON string or `@file.json` path."""
    if items_arg.startswith("@"):
        return cast("list[dict[str, Any]]", json.loads(Path(items_arg[1:]).read_text()))
    return cast("list[dict[str, Any]]", json.loads(items_arg))


@app_config.command(name="bulk-create")
@click.option(
    "--items",
    required=True,
    help="JSON list of `{name, config}` items, or `@path/to/items.json`.",
)
def bulk_create(items: str) -> None:
    """Bulk-create USER-scope fragments; returns recomputed merged views."""
    from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
        MyAppConfigFragmentItemInput,
        MyBulkCreateAppConfigFragmentsInput,
    )

    parsed = [MyAppConfigFragmentItemInput.model_validate(item) for item in _load_items(items)]

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config.my_bulk_create(
                MyBulkCreateAppConfigFragmentsInput(items=parsed),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@app_config.command(name="bulk-update")
@click.option(
    "--items",
    required=True,
    help="Same shape as `bulk-create`; replaces `config` wholesale.",
)
def bulk_update(items: str) -> None:
    """Bulk-update USER-scope fragments; returns recomputed merged views."""
    from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
        MyAppConfigFragmentItemInput,
        MyBulkUpdateAppConfigFragmentsInput,
    )

    parsed = [MyAppConfigFragmentItemInput.model_validate(item) for item in _load_items(items)]

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config.my_bulk_update(
                MyBulkUpdateAppConfigFragmentsInput(items=parsed),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
