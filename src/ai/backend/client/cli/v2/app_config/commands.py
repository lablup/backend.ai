"""CLI commands for app configuration management."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import create_v2_registry, load_v2_config, print_result


@click.group(name="app-config")
def app_config() -> None:
    """App configuration commands."""


# ------------------------------------------------------------------ Domain config


@app_config.command(name="get-domain")
@click.argument("domain_name", type=str)
def get_domain(domain_name: str) -> None:
    """Get domain-level app configuration."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config.get_domain_config(domain_name)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@app_config.command(name="delete-domain")
@click.argument("domain_name", type=str)
def delete_domain(domain_name: str) -> None:
    """Delete domain-level app configuration."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config.delete_domain_config(domain_name)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


# ------------------------------------------------------------------ User config


@app_config.command(name="get-user")
@click.argument("user_id", type=str)
def get_user(user_id: str) -> None:
    """Get user-level app configuration."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config.get_user_config(user_id)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@app_config.command(name="delete-user")
@click.argument("user_id", type=str)
def delete_user(user_id: str) -> None:
    """Delete user-level app configuration."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config.delete_user_config(user_id)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


# ------------------------------------------------------------------ Merged config


@app_config.command(name="get-merged")
@click.argument("user_id", type=str)
def get_merged(user_id: str) -> None:
    """Get merged app configuration for a user."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.app_config.get_merged_config(user_id)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
