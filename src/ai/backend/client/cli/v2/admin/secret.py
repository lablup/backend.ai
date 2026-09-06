"""Admin CLI commands for the stored secrets."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    print_result,
)


@click.group()
def secret() -> None:
    """Admin stored secret commands."""


@secret.command()
def reencrypt() -> None:
    """Encrypt every stored secret again through the write provider (superadmin only)."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            print_result(await registry.secret.admin_reencrypt())
        finally:
            await registry.close()

    asyncio.run(_run())


@secret.command()
def status() -> None:
    """Report the stored secrets per column and key id (superadmin only)."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            print_result(await registry.secret.admin_status())
        finally:
            await registry.close()

    asyncio.run(_run())
