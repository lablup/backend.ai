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
                UpdateSystemSessionEnvironInput(
                    id=SystemSessionEnvironID(environ_id),
                    key=key if key is not None else UNSET,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    run_async(_run)
