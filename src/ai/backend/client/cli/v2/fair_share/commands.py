"""CLI commands for fair share management."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.types import CLIContext
from ai.backend.client.cli.v2.helpers import create_v2_registry, print_result


@click.group()
def fair_share() -> None:
    """Fair share management commands."""


# ========== Domain Fair Share ==========


@fair_share.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@pass_ctx_obj
def search_domain(ctx: CLIContext, limit: int | None, offset: int | None) -> None:
    """Search domain fair shares."""
    from ai.backend.common.dto.manager.v2.fair_share.request import SearchDomainFairSharesInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.fair_share.search_domain(
                SearchDomainFairSharesInput(limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@fair_share.command()
@click.option("--resource-group", required=True, help="Scaling group name.")
@click.option("--domain-name", required=True, help="Domain name.")
@pass_ctx_obj
def get_domain(ctx: CLIContext, resource_group: str, domain_name: str) -> None:
    """Get a single domain fair share record."""
    from ai.backend.common.dto.manager.v2.fair_share.request import GetDomainFairShareInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.fair_share.get_domain(
                GetDomainFairShareInput(
                    resource_group=resource_group,
                    domain_name=domain_name,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


# ========== Project Fair Share ==========


@fair_share.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@pass_ctx_obj
def search_project(ctx: CLIContext, limit: int | None, offset: int | None) -> None:
    """Search project fair shares."""
    from ai.backend.common.dto.manager.v2.fair_share.request import SearchProjectFairSharesInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.fair_share.search_project(
                SearchProjectFairSharesInput(limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@fair_share.command()
@click.option("--resource-group", required=True, help="Scaling group name.")
@click.option("--project-id", required=True, help="Project UUID.")
@pass_ctx_obj
def get_project(ctx: CLIContext, resource_group: str, project_id: str) -> None:
    """Get a single project fair share record."""
    from uuid import UUID

    from ai.backend.common.dto.manager.v2.fair_share.request import GetProjectFairShareInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.fair_share.get_project(
                GetProjectFairShareInput(
                    resource_group=resource_group,
                    project_id=UUID(project_id),
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


# ========== User Fair Share ==========


@fair_share.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@pass_ctx_obj
def search_user(ctx: CLIContext, limit: int | None, offset: int | None) -> None:
    """Search user fair shares."""
    from ai.backend.common.dto.manager.v2.fair_share.request import SearchUserFairSharesInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.fair_share.search_user(
                SearchUserFairSharesInput(limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@fair_share.command()
@click.option("--resource-group", required=True, help="Scaling group name.")
@click.option("--project-id", required=True, help="Project UUID.")
@click.option("--user-uuid", required=True, help="User UUID.")
@pass_ctx_obj
def get_user(ctx: CLIContext, resource_group: str, project_id: str, user_uuid: str) -> None:
    """Get a single user fair share record."""
    from uuid import UUID

    from ai.backend.common.dto.manager.v2.fair_share.request import GetUserFairShareInput

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.fair_share.get_user(
                GetUserFairShareInput(
                    resource_group=resource_group,
                    project_id=UUID(project_id),
                    user_uuid=UUID(user_uuid),
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
