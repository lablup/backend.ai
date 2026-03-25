"""CLI commands for the v2 user resource."""

from __future__ import annotations

import asyncio
import json
import sys
from uuid import UUID

import click

from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.types import CLIContext
from ai.backend.client.cli.v2.helpers import create_v2_registry, print_result


@click.group()
def users() -> None:
    """User management commands."""


@users.command()
@pass_ctx_obj
@click.option("--limit", default=20, help="Maximum number of results to return.")
@click.option("--offset", default=0, help="Number of results to skip.")
def search(ctx: CLIContext, limit: int, offset: int) -> None:
    """Search users (superadmin only)."""
    from ai.backend.common.dto.manager.v2.user.request import AdminSearchUsersInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.user.admin_search(
                AdminSearchUsersInput(limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@users.command()
@pass_ctx_obj
@click.argument("user_id", type=click.UUID)
def get(ctx: CLIContext, user_id: UUID) -> None:
    """Get a user by UUID."""

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.user.get(user_id)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@users.command()
@pass_ctx_obj
@click.argument("body", type=str)
def create(ctx: CLIContext, body: str) -> None:
    """Create a new user (superadmin only).

    BODY is a JSON string with user creation fields.
    """
    from ai.backend.common.dto.manager.v2.user.request import CreateUserInput

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON: {e}", err=True)
        sys.exit(1)

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.user.create(CreateUserInput(**data))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@users.command()
@pass_ctx_obj
@click.argument("user_id", type=click.UUID)
@click.argument("body", type=str)
def update(ctx: CLIContext, user_id: UUID, body: str) -> None:
    """Update a user by UUID (superadmin only).

    BODY is a JSON string with fields to update.
    """
    from ai.backend.common.dto.manager.v2.user.request import UpdateUserInput

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON: {e}", err=True)
        sys.exit(1)

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.user.update(user_id, UpdateUserInput(**data))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@users.command()
@pass_ctx_obj
@click.argument("user_id", type=click.UUID)
def delete(ctx: CLIContext, user_id: UUID) -> None:
    """Soft-delete a user by UUID (superadmin only)."""
    from ai.backend.common.dto.manager.v2.user.request import DeleteUserInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.user.delete(DeleteUserInput(user_id=user_id))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@users.command(name="search-by-domain")
@pass_ctx_obj
@click.argument("domain_name")
@click.option("--limit", default=20, help="Maximum number of results to return.")
@click.option("--offset", default=0, help="Number of results to skip.")
def search_by_domain(ctx: CLIContext, domain_name: str, limit: int, offset: int) -> None:
    """Search users within a specific domain."""
    from ai.backend.common.dto.manager.v2.user.request import SearchUsersRequest

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.user.search_by_domain(
                domain_name,
                SearchUsersRequest(limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@users.command(name="search-by-project")
@pass_ctx_obj
@click.argument("project_id", type=click.UUID)
@click.option("--limit", default=20, help="Maximum number of results to return.")
@click.option("--offset", default=0, help="Number of results to skip.")
def search_by_project(ctx: CLIContext, project_id: UUID, limit: int, offset: int) -> None:
    """Search users within a specific project."""
    from ai.backend.common.dto.manager.v2.user.request import SearchUsersRequest

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.user.search_by_project(
                project_id,
                SearchUsersRequest(limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@users.command(name="search-by-role")
@pass_ctx_obj
@click.argument("role_id", type=click.UUID)
@click.option("--limit", default=20, help="Maximum number of results to return.")
@click.option("--offset", default=0, help="Number of results to skip.")
def search_by_role(ctx: CLIContext, role_id: UUID, limit: int, offset: int) -> None:
    """Search users with a specific role."""
    from ai.backend.common.dto.manager.v2.user.request import SearchUsersRequest

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.user.search_by_role(
                role_id,
                SearchUsersRequest(limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
