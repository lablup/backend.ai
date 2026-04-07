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
@click.argument("session_id", type=click.UUID)
def get(session_id: UUID) -> None:
    """Get a session by ID."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.session.get(session_id)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@session.command(name="project-search")
@click.argument("project_id", type=click.UUID)
@click.option("--limit", type=int, default=20)
@click.option("--offset", type=int, default=0)
def project_search(project_id: UUID, limit: int, offset: int) -> None:
    """Search sessions within a project."""

    from ai.backend.common.dto.manager.v2.session.request import AdminSearchSessionsInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            request = AdminSearchSessionsInput(limit=limit, offset=offset)
            result = await registry.session.project_search(project_id, request)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@session.command()
@click.argument("session_ids", nargs=-1, required=True, type=click.UUID)
@click.option("--forced", is_flag=True, default=False, help="Force-terminate without cleanup.")
def terminate(session_ids: tuple[UUID, ...], forced: bool) -> None:
    """Terminate one or more sessions by ID."""

    from ai.backend.common.dto.manager.v2.session.request import TerminateSessionsInput

    body = TerminateSessionsInput(
        session_ids=list(session_ids),
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
@click.argument("session_id", type=click.UUID)
@click.argument("service", type=str)
@click.option("--port", type=int, default=None, help="Specific container port.")
@click.option(
    "--owner-id",
    type=click.UUID,
    default=None,
    help="Delegated owner user UUID. Defaults to the caller when omitted.",
)
def start_service(session_id: UUID, service: str, port: int | None, owner_id: UUID | None) -> None:
    """Start a service (e.g., jupyter, vscode) in a session."""

    from ai.backend.common.dto.manager.v2.session.request import StartSessionServiceInput

    body = StartSessionServiceInput(service=service, port=port, owner_id=owner_id)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.session.start_service(session_id, body)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@session.command(name="shutdown-service")
@click.argument("session_id", type=click.UUID)
@click.argument("service", type=str)
@click.option(
    "--owner-id",
    type=click.UUID,
    default=None,
    help="Delegated owner user UUID. Defaults to the caller when omitted.",
)
def shutdown_service(session_id: UUID, service: str, owner_id: UUID | None) -> None:
    """Shut down a service in a session."""

    from ai.backend.common.dto.manager.v2.session.request import ShutdownSessionServiceInput

    body = ShutdownSessionServiceInput(service=service, owner_id=owner_id)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            await registry.session.shutdown_service(session_id, body)
            click.echo("Service shut down successfully.")
        finally:
            await registry.close()

    asyncio.run(_run())


@session.command()
@click.argument("session_id", type=click.UUID)
@click.option(
    "--owner-id",
    type=click.UUID,
    default=None,
    help="Delegated owner user UUID. Defaults to the caller when omitted.",
)
def restart(session_id: UUID, owner_id: UUID | None) -> None:
    """Restart a session."""

    from ai.backend.common.dto.manager.v2.session.request import RestartSessionInput

    body = RestartSessionInput(owner_id=owner_id)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.session.restart(session_id, body)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@session.command()
@click.argument("session_id", type=click.UUID)
@click.option("--forced", is_flag=True, default=False, help="Force-destroy without cleanup.")
@click.option("--recursive", is_flag=True, default=False, help="Destroy dependent sessions too.")
@click.option(
    "--owner-id",
    type=click.UUID,
    default=None,
    help="Delegated owner user UUID. Defaults to the caller when omitted.",
)
def destroy(session_id: UUID, forced: bool, recursive: bool, owner_id: UUID | None) -> None:
    """Destroy a session."""

    from ai.backend.common.dto.manager.v2.session.request import DestroySessionInput

    body = DestroySessionInput(forced=forced, recursive=recursive, owner_id=owner_id)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.session.destroy(session_id, body)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@session.command()
@click.argument("session_id", type=click.UUID)
@click.option("--kernel-id", type=click.UUID, default=None, help="Specific kernel UUID.")
@click.option(
    "--owner-id",
    type=click.UUID,
    default=None,
    help="Delegated owner user UUID. Defaults to the caller when omitted.",
)
def logs(session_id: UUID, kernel_id: UUID | None, owner_id: UUID | None) -> None:
    """Get container logs for a session."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.session.get_logs(session_id, kernel_id, owner_id)
            click.echo(result.logs)
        finally:
            await registry.close()

    asyncio.run(_run())


@session.command()
@click.argument("session_id", type=click.UUID)
@click.option("--name", type=str, default=None, help="New session name.")
@click.option("--tag", type=str, default=None, help="Updated tag.")
@click.option(
    "--owner-id",
    type=click.UUID,
    default=None,
    help="Delegated owner user UUID. Defaults to the caller when omitted.",
)
def update(session_id: UUID, name: str | None, tag: str | None, owner_id: UUID | None) -> None:
    """Update a session."""

    from ai.backend.common.dto.manager.v2.session.request import UpdateSessionInput

    body = UpdateSessionInput(name=name, tag=tag, owner_id=owner_id)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.session.update(session_id, body)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
