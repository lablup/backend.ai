"""CLI commands for SSH keys."""

from __future__ import annotations

import asyncio
from uuid import UUID

import click

from ai.backend.client.cli.v2.helpers import create_v2_registry, load_v2_config, print_result


@click.group()
def ssh_key() -> None:
    """SSH key commands."""


@ssh_key.command(name="switch-default")
@click.argument("ssh_key_id", type=click.UUID)
def switch_default(ssh_key_id: UUID) -> None:
    """Make an SSH key the default of its owner."""
    from ai.backend.common.data.entity.ssh_keypair import SSHKeypairID

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.ssh_key.switch_default(SSHKeypairID(ssh_key_id))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
