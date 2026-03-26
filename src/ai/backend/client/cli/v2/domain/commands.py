"""CLI commands for the v2 domain resource.

User-facing commands only. Admin commands are in admin/domain.py.
"""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import create_v2_registry, load_v2_config, print_result


@click.group()
def domain() -> None:
    """Domain commands."""


@domain.command()
@click.argument("domain_name")
def get(domain_name: str) -> None:
    """Get a domain by name."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.domain.get(domain_name)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
