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
