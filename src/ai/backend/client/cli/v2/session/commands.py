"""User-facing CLI commands for the v2 session domain."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from uuid import UUID

import click

from ai.backend.client.cli.v2.helpers import create_v2_registry, load_v2_config, print_result


@click.group()
def session() -> None:
    """Session management commands."""


@session.command()
@click.argument("payload", type=str)
def enqueue(payload: str) -> None:
    """Enqueue a new compute session.

    PAYLOAD is a JSON string or @file path containing the EnqueueSessionInput body.
    """

    from ai.backend.common.dto.manager.v2.session.request import EnqueueSessionInput

    if payload.startswith("@"):
        with Path(payload[1:]).open() as f:
            data = json.load(f)
    else:
        data = json.loads(payload)
    body = EnqueueSessionInput.model_validate(data)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.session.enqueue(body)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@session.command()
@click.argument("session_id", type=str)
def get(session_id: str) -> None:
    """Get a session by ID."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.session.get(UUID(session_id))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@session.command(name="project-search")
@click.argument("project_id", type=str)
@click.option("--limit", type=int, default=20)
@click.option("--offset", type=int, default=0)
def project_search(project_id: str, limit: int, offset: int) -> None:
    """Search sessions within a project."""

    from ai.backend.common.dto.manager.v2.session.request import AdminSearchSessionsInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            request = AdminSearchSessionsInput(limit=limit, offset=offset)
            result = await registry.session.project_search(UUID(project_id), request)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
