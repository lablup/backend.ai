"""User-facing CLI commands for the system session environ domain."""

from __future__ import annotations

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
