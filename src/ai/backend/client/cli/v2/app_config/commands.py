"""CLI commands for app configuration management."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.extensions import pass_ctx_obj
from ai.backend.client.cli.types import CLIContext
from ai.backend.client.cli.v2.helpers import create_v2_registry, print_result


@click.group()
def app_configs() -> None:
    """App configuration commands."""


# ------------------------------------------------------------------ Domain config


@app_configs.command()
@click.argument("domain_name", type=str)
@pass_ctx_obj
def get_domain(ctx: CLIContext, domain_name: str) -> None:
    """Get domain-level app configuration."""

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.app_config.get_domain_config(domain_name)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@app_configs.command()
@click.argument("domain_name", type=str)
@pass_ctx_obj
def delete_domain(ctx: CLIContext, domain_name: str) -> None:
    """Delete domain-level app configuration."""

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.app_config.delete_domain_config(domain_name)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


# ------------------------------------------------------------------ User config


@app_configs.command()
@click.argument("user_id", type=str)
@pass_ctx_obj
def get_user(ctx: CLIContext, user_id: str) -> None:
    """Get user-level app configuration."""

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.app_config.get_user_config(user_id)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@app_configs.command()
@click.argument("user_id", type=str)
@pass_ctx_obj
def delete_user(ctx: CLIContext, user_id: str) -> None:
    """Delete user-level app configuration."""

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.app_config.delete_user_config(user_id)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


# ------------------------------------------------------------------ Merged config


@app_configs.command()
@click.argument("user_id", type=str)
@pass_ctx_obj
def get_merged(ctx: CLIContext, user_id: str) -> None:
    """Get merged app configuration for a user."""

    async def _run() -> None:
        registry = await create_v2_registry(ctx)
        try:
            result = await registry.app_config.get_merged_config(user_id)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
