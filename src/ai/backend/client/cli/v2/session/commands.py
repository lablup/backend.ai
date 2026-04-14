"""User-facing CLI commands for the v2 session domain."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from uuid import UUID

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    print_result,
)


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


@session.command()
@click.argument("session_ids", nargs=-1, required=True)
@click.option("--forced", is_flag=True, default=False, help="Force-terminate without cleanup.")
def terminate(session_ids: tuple[str, ...], forced: bool) -> None:
    """Terminate one or more sessions by ID."""

    from ai.backend.common.dto.manager.v2.session.request import TerminateSessionsInput

    body = TerminateSessionsInput(
        session_ids=[UUID(sid) for sid in session_ids],
        forced=forced,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.session.terminate(body)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@session.command(name="start-service")
@click.argument("session_id", type=str)
@click.argument("service", type=str)
@click.option("--port", type=int, default=None, help="Specific container port.")
def start_service(session_id: str, service: str, port: int | None) -> None:
    """Start a service (e.g., jupyter, vscode) in a session."""

    from ai.backend.common.dto.manager.v2.session.request import StartSessionServiceInput

    body = StartSessionServiceInput(service=service, port=port)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.session.start_service(UUID(session_id), body)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@session.command(name="shutdown-service")
@click.argument("session_id", type=str)
@click.argument("service", type=str)
def shutdown_service(session_id: str, service: str) -> None:
    """Shut down a service in a session."""

    from ai.backend.common.dto.manager.v2.session.request import ShutdownSessionServiceInput

    body = ShutdownSessionServiceInput(service=service)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            await registry.session.shutdown_service(UUID(session_id), body)
            click.echo("Service shut down successfully.")
        finally:
            await registry.close()

    asyncio.run(_run())


@session.command()
@click.argument("session_id", type=str)
@click.option("--kernel-id", type=str, default=None, help="Specific kernel UUID.")
def logs(session_id: str, kernel_id: str | None) -> None:
    """Get container logs for a session."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.session.get_logs(
                UUID(session_id),
                UUID(kernel_id) if kernel_id else None,
            )
            click.echo(result.logs)
        finally:
            await registry.close()

    asyncio.run(_run())


@session.command()
@click.argument("session_id", type=str)
@click.option("--name", type=str, default=None, help="New session name.")
@click.option("--tag", type=str, default=None, help="Updated tag.")
def update(session_id: str, name: str | None, tag: str | None) -> None:
    """Update a session."""

    from ai.backend.common.dto.manager.v2.session.request import UpdateSessionInput

    body = UpdateSessionInput(name=name, tag=tag)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.session.update(UUID(session_id), body)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
