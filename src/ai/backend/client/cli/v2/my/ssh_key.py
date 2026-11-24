"""CLI commands for self-service SSH key operations."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import create_v2_registry, load_v2_config, print_result


@click.group()
def ssh_key() -> None:
    """My SSH key commands."""


@ssh_key.command()
@click.option(
    "--public-key",
    required=True,
    type=str,
    help=(
        "The SSH public key in the OpenSSH single-line format. It becomes the default only "
        "when you have no default yet."
    ),
)
def upload(public_key: str) -> None:
    """Upload a public key to my SSH keys."""
    from ai.backend.common.dto.manager.v2.ssh_key.request import MyUploadSSHKeyInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.ssh_key.my_upload(MyUploadSSHKeyInput(public_key=public_key))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@ssh_key.command()
@click.option(
    "--default/--not-default",
    "is_default",
    default=None,
    help="Filter by whether sessions use the SSH key.",
)
@click.option("--limit", type=int, default=20, help="Maximum number of items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
def search(is_default: bool | None, limit: int, offset: int) -> None:
    """Search my SSH keys."""
    from ai.backend.common.dto.manager.v2.ssh_key.request import (
        MySearchSSHKeysInput,
        SSHKeyFilter,
    )

    request = MySearchSSHKeysInput(
        filter=SSHKeyFilter(is_default=is_default), limit=limit, offset=offset
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            print_result(await registry.ssh_key.my_search(request))
        finally:
            await registry.close()

    asyncio.run(_run())
