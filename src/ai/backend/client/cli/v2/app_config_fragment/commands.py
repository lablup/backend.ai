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
    AppConfigScopeRef,
)
from ai.backend.common.identifier.app_config import AppConfigScopeID
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID


@click.group()
def app_config_fragment() -> None:
    """App config fragment commands."""


def _resolve_scope(scope_type: str, scope_id: uuid.UUID | None) -> AppConfigScopeRef:
    """The scope the request acts at, rejecting a scope-id that does not match its kind.

    ``public`` is one global scope owning no id, while ``domain`` and ``user`` are each
    identified by their owner. The server rejects a mismatch too, but only after the request
    is on the wire, and as a validation error rather than a usage message.
    """
    resolved_type = AppConfigScopeType(scope_type)
    match resolved_type:
        case AppConfigScopeType.PUBLIC:
            if scope_id is not None:
                raise click.UsageError(
                    "--scope-id must be omitted for the public scope, which has no owner."
                )
            return AppConfigScopeRef(scope_type=resolved_type, scope_id=None)
        case AppConfigScopeType.DOMAIN | AppConfigScopeType.USER:
            if scope_id is None:
                raise click.UsageError(
                    f"--scope-id is required for the {resolved_type.value} scope."
                )
            return AppConfigScopeRef(scope_type=resolved_type, scope_id=AppConfigScopeID(scope_id))


@app_config_fragment.command()
@click.option(
    "--scope-type",
    required=True,
    type=click.Choice([scope_type.value for scope_type in AppConfigScopeType]),
    help="Scope whose fragments to read (public | domain | user).",
)
@click.option(
    "--scope-id",
    default=None,
    type=click.UUID,
    help="Domain id or user id; omit for the public scope.",
)
@click.argument("config_names", nargs=-1, required=True)
def get(scope_type: str, scope_id: uuid.UUID | None, config_names: tuple[str, ...]) -> None:
    """Read one scope's fragments for CONFIG_NAMES, answered in that order.

    A name the scope holds no fragment for is answered as null, so the result lines up
    position by position with CONFIG_NAMES. Only fragments written at this scope are
    answered — scopes do not inherit from one another.
    """
    scope = _resolve_scope(scope_type, scope_id)

    async def _run() -> None:
        from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
            ScopedAppConfigFragmentsByNamesInput,
        )

        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config_fragment.scoped_get_app_config_fragments_by_names(
                ScopedAppConfigFragmentsByNamesInput(scope=scope, config_names=list(config_names))
            )
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)


@app_config_fragment.command()
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
def update(scope_type: str, scope_id: uuid.UUID | None, items: str) -> None:
    """Write the given configs' fragments at one scope, reporting each item's outcome.

    Each item replaces the scope's fragment for its config name, or creates it when the
    scope holds none. A rejected item fails alone and the rest of the batch lands.
    """
    from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
        ScopedUpsertAppConfigFragmentsInput,
    )

    scope = _resolve_scope(scope_type, scope_id)
    parsed_items = load_model(items, list[AppConfigFragmentUpsertItem])

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config_fragment.scoped_bulk_upsert_app_config_fragments(
                ScopedUpsertAppConfigFragmentsInput(scope=scope, items=parsed_items)
            )
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)


@app_config_fragment.command()
@click.option(
    "--id",
    "fragment_id",
    required=True,
    type=click.UUID,
    help="Id of the fragment to purge, as answered by a read or an admin search.",
)
def purge(fragment_id: uuid.UUID) -> None:
    """Purge an app config fragment by id."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config_fragment.purge(AppConfigFragmentID(fragment_id))
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)


@app_config_fragment.command(name="bulk-purge")
@click.option(
    "--id",
    "ids",
    required=True,
    multiple=True,
    type=click.UUID,
    help="Fragment id to purge. Repeat for more.",
)
def bulk_purge(ids: tuple[uuid.UUID, ...]) -> None:
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
