"""User-facing CLI commands for the system session environ domain."""

from __future__ import annotations

from uuid import UUID

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    print_result,
    run_async,
)


@click.group(name="system-session-environ")
def system_session_environ() -> None:
    """System session environ commands."""


@system_session_environ.command(name="value-sources")
def value_sources() -> None:
    """List every value source a system session environ row can carry."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.system_session_environ.list_value_sources()
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)


@system_session_environ.command()
@click.option("--key", type=str, required=True, help="Environment variable name.")
@click.option(
    "--value-source",
    type=str,
    required=True,
    help="Value source name, as `value-sources` lists.",
)
@click.option(
    "--scope-type",
    type=click.Choice(["public", "domain", "project"]),
    required=True,
    help="Whether the row applies to every session, a domain's or a project's.",
)
@click.option(
    "--scope-id",
    type=click.UUID,
    default=None,
    help="Domain or project id. Left out for public.",
)
def create(key: str, value_source: str, scope_type: str, scope_id: UUID | None) -> None:
    """Bind a value source to an environment variable name at one scope."""
    from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironScopeID
    from ai.backend.common.dto.manager.v2.system_session_environ.request import (
        CreateSystemSessionEnvironInput,
    )
    from ai.backend.common.dto.manager.v2.system_session_environ.types import (
        SystemSessionEnvironScopeType,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.system_session_environ.create(
                CreateSystemSessionEnvironInput(
                    key=key,
                    value_source=value_source,
                    scope_type=SystemSessionEnvironScopeType(scope_type),
                    scope_id=SystemSessionEnvironScopeID(scope_id)
                    if scope_id is not None
                    else None,
                )
            )
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)


@system_session_environ.command()
@click.argument("environ_id", type=click.UUID)
@click.option("--key", type=str, default=None, help="New environment variable name.")
def update(environ_id: UUID, key: str | None) -> None:
    """Change a system session environ row's key."""
    from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironID
    from ai.backend.common.dto.manager.v2.system_session_environ.request import (
        UpdateSystemSessionEnvironInput,
    )
    from ai.backend.common.tristate.unset import UNSET

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.system_session_environ.update(
                SystemSessionEnvironID(environ_id),
                UpdateSystemSessionEnvironInput(key=key if key is not None else UNSET),
            )
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)


@system_session_environ.command()
@click.argument("environ_id", type=click.UUID)
def delete(environ_id: UUID) -> None:
    """Soft-delete a system session environ row."""
    from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironID

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.system_session_environ.delete(
                SystemSessionEnvironID(environ_id)
            )
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)


@system_session_environ.command()
@click.argument("environ_id", type=click.UUID)
def restore(environ_id: UUID) -> None:
    """Restore a soft-deleted system session environ row."""
    from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironID

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.system_session_environ.restore(
                SystemSessionEnvironID(environ_id)
            )
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)


@system_session_environ.command()
@click.argument("environ_id", type=click.UUID)
def purge(environ_id: UUID) -> None:
    """Remove a system session environ row for good, soft-deleted or not."""
    from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironID

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.system_session_environ.purge(SystemSessionEnvironID(environ_id))
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)
