"""CLI commands for RBAC management."""

from __future__ import annotations

import asyncio
from uuid import UUID

import click

from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.types import CLIContext
from ai.backend.client.cli.v2.helpers import create_v2_registry, print_result


@click.group()
def rbac() -> None:
    """RBAC management commands."""


# ------------------------------------------------------------------ Roles


@rbac.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@pass_ctx_obj
def search_roles(ctx: CLIContext, limit: int | None, offset: int | None) -> None:
    """Search roles."""
    from ai.backend.common.dto.manager.v2.rbac.request import AdminSearchRolesGQLInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.rbac.search_roles(
                AdminSearchRolesGQLInput(limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@rbac.command()
@click.argument("role_id", type=str)
@pass_ctx_obj
def get_role(ctx: CLIContext, role_id: str) -> None:
    """Get a role by UUID."""

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.rbac.get_role(UUID(role_id))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@rbac.command()
@click.option("--name", required=True, help="Role name.")
@click.option("--description", default=None, help="Role description.")
@pass_ctx_obj
def create_role(ctx: CLIContext, name: str, description: str | None) -> None:
    """Create a new role."""
    from ai.backend.common.dto.manager.v2.rbac.request import CreateRoleInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.rbac.create_role(
                CreateRoleInput(name=name, description=description),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@rbac.command()
@click.argument("role_id", type=str)
@pass_ctx_obj
def delete_role(ctx: CLIContext, role_id: str) -> None:
    """Soft-delete a role."""
    from ai.backend.common.dto.manager.v2.rbac.request import DeleteRoleInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.rbac.delete_role(
                DeleteRoleInput(id=UUID(role_id)),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


# ------------------------------------------------------------------ Permissions


@rbac.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@pass_ctx_obj
def search_permissions(ctx: CLIContext, limit: int | None, offset: int | None) -> None:
    """Search permissions."""
    from ai.backend.common.dto.manager.v2.rbac.request import AdminSearchPermissionsGQLInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.rbac.search_permissions(
                AdminSearchPermissionsGQLInput(limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


# ------------------------------------------------------------------ Assignments


@rbac.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@pass_ctx_obj
def search_assignments(ctx: CLIContext, limit: int | None, offset: int | None) -> None:
    """Search role assignments."""
    from ai.backend.common.dto.manager.v2.rbac.request import AdminSearchRoleAssignmentsGQLInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.rbac.search_assignments(
                AdminSearchRoleAssignmentsGQLInput(limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@rbac.command()
@click.option("--user-id", required=True, help="User UUID to assign the role to.")
@click.option("--role-id", required=True, help="Role UUID to assign.")
@pass_ctx_obj
def assign_role(ctx: CLIContext, user_id: str, role_id: str) -> None:
    """Assign a role to a user."""
    from ai.backend.common.dto.manager.v2.rbac.request import AssignRoleInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.rbac.assign_role(
                AssignRoleInput(user_id=UUID(user_id), role_id=UUID(role_id)),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@rbac.command()
@click.option("--user-id", required=True, help="User UUID to revoke the role from.")
@click.option("--role-id", required=True, help="Role UUID to revoke.")
@pass_ctx_obj
def revoke_role(ctx: CLIContext, user_id: str, role_id: str) -> None:
    """Revoke a role from a user."""
    from ai.backend.common.dto.manager.v2.rbac.request import RevokeRoleInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.rbac.revoke_role(
                RevokeRoleInput(user_id=UUID(user_id), role_id=UUID(role_id)),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


# ------------------------------------------------------------------ Entities


@rbac.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@pass_ctx_obj
def search_entities(ctx: CLIContext, limit: int | None, offset: int | None) -> None:
    """Search entity associations."""
    from ai.backend.common.dto.manager.v2.rbac.request import AdminSearchEntitiesGQLInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.rbac.search_entities(
                AdminSearchEntitiesGQLInput(limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
