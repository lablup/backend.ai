"""CLI commands for the v2 session domain."""

from __future__ import annotations

import asyncio
from typing import Any

import click

from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.types import CLIContext
from ai.backend.client.cli.v2._helpers import create_v2_registry, print_result


@click.group()
def sessions() -> None:
    """Session management commands."""


@sessions.command()
@pass_ctx_obj
@click.option("--limit", type=int, default=20, help="Maximum number of items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
@click.option("--filter", "filter_json", default=None, help="JSON filter expression.")
def search(ctx: CLIContext, limit: int, offset: int, filter_json: str | None) -> None:
    """Search sessions with admin scope."""
    from ai.backend.common.dto.manager.v2.session.request import AdminSearchSessionsInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            kwargs: dict[str, Any] = {"limit": limit, "offset": offset}
            if filter_json is not None:
                import json

                kwargs["filter"] = json.loads(filter_json)
            request = AdminSearchSessionsInput(**kwargs)
            result = await registry.session.admin_search(request)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@sessions.command(name="search-kernels")
@pass_ctx_obj
@click.option("--limit", type=int, default=20, help="Maximum number of items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
@click.option("--filter", "filter_json", default=None, help="JSON filter expression.")
def search_kernels(ctx: CLIContext, limit: int, offset: int, filter_json: str | None) -> None:
    """Search kernels with admin scope."""
    from ai.backend.common.dto.manager.v2.kernel.request import AdminSearchKernelsInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            kwargs: dict[str, Any] = {"limit": limit, "offset": offset}
            if filter_json is not None:
                import json

                kwargs["filter"] = json.loads(filter_json)
            request = AdminSearchKernelsInput(**kwargs)
            result = await registry.session.admin_search_kernels(request)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@sessions.command(name="search-by-agent")
@pass_ctx_obj
@click.argument("agent_id")
@click.option("--limit", type=int, default=20, help="Maximum number of items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
def search_by_agent(ctx: CLIContext, agent_id: str, limit: int, offset: int) -> None:
    """Search sessions scoped to a specific agent."""
    from ai.backend.common.dto.manager.v2.session.request import AdminSearchSessionsInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            request = AdminSearchSessionsInput(limit=limit, offset=offset)
            result = await registry.session.search_sessions_by_agent(agent_id, request)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@sessions.command(name="search-kernels-by-agent")
@pass_ctx_obj
@click.argument("agent_id")
@click.option("--limit", type=int, default=20, help="Maximum number of items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
def search_kernels_by_agent(ctx: CLIContext, agent_id: str, limit: int, offset: int) -> None:
    """Search kernels scoped to a specific agent."""
    from ai.backend.common.dto.manager.v2.kernel.request import AdminSearchKernelsInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            request = AdminSearchKernelsInput(limit=limit, offset=offset)
            result = await registry.session.search_kernels_by_agent(agent_id, request)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@sessions.command(name="search-kernels-by-session")
@pass_ctx_obj
@click.argument("session_id")
@click.option("--limit", type=int, default=20, help="Maximum number of items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
def search_kernels_by_session(ctx: CLIContext, session_id: str, limit: int, offset: int) -> None:
    """Search kernels scoped to a specific session."""
    from ai.backend.common.dto.manager.v2.kernel.request import AdminSearchKernelsInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            request = AdminSearchKernelsInput(limit=limit, offset=offset)
            result = await registry.session.search_kernels_by_session(session_id, request)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
