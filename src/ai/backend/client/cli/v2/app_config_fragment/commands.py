"""CLI commands for app config fragments (scoped reads, writes and purges)."""

from __future__ import annotations

import uuid

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_model,
    load_v2_config,
    print_result,
    run_async,
)
from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    AppConfigFragmentUpsertItem,
)
from ai.backend.common.identifier.app_config import AppConfigScopeID
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID


@click.group()
def app_config_fragment() -> None:
    """App config fragment commands."""


@app_config_fragment.command(name="by-names")
@click.option(
    "--scope-type",
    required=True,
    type=click.Choice([scope_type.value for scope_type in AppConfigScopeType]),
    help="Scope the fragments are written at (public | domain | user).",
)
@click.option(
    "--scope-id",
    default=None,
    type=click.UUID,
    help="Domain id or user id; omit for the public scope.",
)
@click.argument("config_names", nargs=-1, required=True)
def by_names(scope_type: str, scope_id: uuid.UUID | None, config_names: tuple[str, ...]) -> None:
    """Read one scope's fragments for CONFIG_NAMES, answered in that order."""
    from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
        AppConfigScopeRef,
        ScopedAppConfigFragmentsByNamesInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config_fragment.scoped_get_app_config_fragments_by_names(
                ScopedAppConfigFragmentsByNamesInput(
                    scope=AppConfigScopeRef(
                        scope_type=AppConfigScopeType(scope_type),
                        scope_id=AppConfigScopeID(scope_id) if scope_id is not None else None,
                    ),
                    config_names=list(config_names),
                )
            )
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)


@app_config_fragment.command(name="bulk-upsert")
@click.option(
    "--scope-type",
    required=True,
    type=click.Choice([scope_type.value for scope_type in AppConfigScopeType]),
    help="Scope the fragments are written at (public | domain | user).",
)
@click.option(
    "--scope-id",
    default=None,
    type=click.UUID,
    help="Domain id or user id; omit for the public scope.",
)
@click.option(
    "--items",
    required=True,
    help=(
        'JSON array of {"config_name": ..., "config": {...}} objects, or @path to a file '
        "holding it."
    ),
)
def bulk_upsert(scope_type: str, scope_id: uuid.UUID | None, items: str) -> None:
    """Upsert many fragments at one scope, all-or-nothing."""
    from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
        AppConfigScopeRef,
        ScopedUpsertAppConfigFragmentsInput,
    )

    parsed_items = load_model(items, list[AppConfigFragmentUpsertItem])

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config_fragment.scoped_bulk_upsert_app_config_fragments(
                ScopedUpsertAppConfigFragmentsInput(
                    scope=AppConfigScopeRef(
                        scope_type=AppConfigScopeType(scope_type),
                        scope_id=AppConfigScopeID(scope_id) if scope_id is not None else None,
                    ),
                    items=parsed_items,
                )
            )
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)


@app_config_fragment.command()
@click.argument("app_config_fragment_id", type=click.UUID)
def get(app_config_fragment_id: uuid.UUID) -> None:
    """Get an app config fragment by id."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config_fragment.get(app_config_fragment_id)
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)


@app_config_fragment.command()
@click.argument("app_config_fragment_id", type=click.UUID)
def purge(app_config_fragment_id: uuid.UUID) -> None:
    """Purge an app config fragment by id."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config_fragment.purge(app_config_fragment_id)
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)


@app_config_fragment.command(name="bulk-delete")
@click.option(
    "--id",
    "ids",
    required=True,
    multiple=True,
    type=click.UUID,
    help="Fragment id to purge. Repeat for more.",
)
def bulk_delete(ids: tuple[uuid.UUID, ...]) -> None:
    """Purge many fragments by id, reporting each item's outcome."""
    from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
        BulkPurgeAppConfigFragmentInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config_fragment.bulk_purge(
                BulkPurgeAppConfigFragmentInput(
                    ids=[AppConfigFragmentID(fragment_id) for fragment_id in ids]
                )
            )
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)
