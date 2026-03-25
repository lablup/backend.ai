"""CLI commands for scheduling history management."""

from __future__ import annotations

import asyncio
from uuid import UUID

import click

from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.types import CLIContext
from ai.backend.client.cli.v2.helpers import create_v2_registry, print_result


@click.group()
def scheduling_history() -> None:
    """Scheduling history commands."""


# ========== Session History ==========


@scheduling_history.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@pass_ctx_obj
def search_sessions(ctx: CLIContext, limit: int | None, offset: int | None) -> None:
    """Search session scheduling histories."""
    from ai.backend.common.dto.manager.v2.scheduling_history.request import (
        AdminSearchSessionHistoriesInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.scheduling_history.search_session_history(
                AdminSearchSessionHistoriesInput(limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@scheduling_history.command()
@click.argument("session_id", type=str)
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@pass_ctx_obj
def search_session(ctx: CLIContext, session_id: str, limit: int | None, offset: int | None) -> None:
    """Search scheduling history for a specific session."""
    from ai.backend.common.dto.manager.v2.scheduling_history.request import (
        AdminSearchSessionHistoriesInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.scheduling_history.session_scoped_search(
                UUID(session_id),
                AdminSearchSessionHistoriesInput(limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


# ========== Deployment History ==========


@scheduling_history.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@pass_ctx_obj
def search_deployments(ctx: CLIContext, limit: int | None, offset: int | None) -> None:
    """Search deployment scheduling histories."""
    from ai.backend.common.dto.manager.v2.scheduling_history.request import (
        AdminSearchDeploymentHistoriesInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.scheduling_history.search_deployment_history(
                AdminSearchDeploymentHistoriesInput(limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@scheduling_history.command()
@click.argument("deployment_id", type=str)
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@pass_ctx_obj
def search_deployment(
    ctx: CLIContext, deployment_id: str, limit: int | None, offset: int | None
) -> None:
    """Search scheduling history for a specific deployment."""
    from ai.backend.common.dto.manager.v2.scheduling_history.request import (
        AdminSearchDeploymentHistoriesInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.scheduling_history.deployment_scoped_search(
                UUID(deployment_id),
                AdminSearchDeploymentHistoriesInput(limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


# ========== Route History ==========


@scheduling_history.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@pass_ctx_obj
def search_routes(ctx: CLIContext, limit: int | None, offset: int | None) -> None:
    """Search route scheduling histories."""
    from ai.backend.common.dto.manager.v2.scheduling_history.request import (
        AdminSearchRouteHistoriesInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.scheduling_history.search_route_history(
                AdminSearchRouteHistoriesInput(limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@scheduling_history.command()
@click.argument("route_id", type=str)
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@pass_ctx_obj
def search_route(ctx: CLIContext, route_id: str, limit: int | None, offset: int | None) -> None:
    """Search scheduling history for a specific route."""
    from ai.backend.common.dto.manager.v2.scheduling_history.request import (
        AdminSearchRouteHistoriesInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.scheduling_history.route_scoped_search(
                UUID(route_id),
                AdminSearchRouteHistoriesInput(limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
