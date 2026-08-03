"""Self-service CLI commands for the caller's own user-scope app config fragments."""

from __future__ import annotations

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_model,
    load_v2_config,
    print_result,
    run_async,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    AppConfigFragmentUpsertItem,
)


@click.group()
def app_config_fragment() -> None:
    """My app config fragment commands."""


@app_config_fragment.command()
@click.argument("config_names", nargs=-1, required=True)
def get(config_names: tuple[str, ...]) -> None:
    """Read my user-scope fragments for CONFIG_NAMES, answered in that order.

    A name my scope holds no fragment for is answered as null, so the result lines up
    position by position with CONFIG_NAMES.
    """
    from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
        MyAppConfigFragmentsByNamesInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config_fragment.my_get_app_config_fragments_by_names(
                MyAppConfigFragmentsByNamesInput(config_names=list(config_names))
            )
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)


@app_config_fragment.command(name="bulk-upsert")
@click.option(
    "--items",
    required=True,
    help=(
        'JSON array of {"config_name": ..., "config": {...}} objects, or @path to a file '
        "holding it."
    ),
)
def bulk_upsert(items: str) -> None:
    """Upsert many fragments at my own user scope, all-or-nothing."""
    from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
        MyUpsertAppConfigFragmentsInput,
    )

    parsed_items = load_model(items, list[AppConfigFragmentUpsertItem])

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config_fragment.my_bulk_upsert_app_config_fragments(
                MyUpsertAppConfigFragmentsInput(items=parsed_items)
            )
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)
