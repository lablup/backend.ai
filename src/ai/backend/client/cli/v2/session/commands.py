"""User-facing CLI commands for the v2 session domain."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import click

from ai.backend.client.cli.v2.helpers import create_v2_registry, load_v2_config, print_result


@click.group()
def session() -> None:
    """Session management commands."""


@session.command()
@click.argument("payload", type=str)
def create(payload: str) -> None:
    """Create a new compute session.

    PAYLOAD is a JSON string or @file path containing the CreateSessionInput body.
    """

    from ai.backend.common.dto.manager.v2.session.request import CreateSessionInput

    if payload.startswith("@"):
        with Path(payload[1:]).open() as f:
            data = json.load(f)
    else:
        data = json.loads(payload)
    body = CreateSessionInput.model_validate(data)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.session.create(body)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
