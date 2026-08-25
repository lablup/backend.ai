from __future__ import annotations

import asyncio
import base64
import contextlib
import logging
import secrets
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

import click
from tabulate import tabulate

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.secret.types import SecretSweepStatus
from ai.backend.manager.secret.keys import KEY_SIZE

if TYPE_CHECKING:
    from ai.backend.manager.repositories.secret.repository import SecretRepository

    from .context import CLIContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_STATUS_COLUMNS = ("provider type", "key id", "count")
# Stands for the key id of a plaintext row, which names no provider key.
_ABSENT = "-"


@click.group()
def cli() -> None:
    pass


@contextlib.asynccontextmanager
async def _repository_ctx(cli_ctx: CLIContext) -> AsyncIterator[SecretRepository]:
    """Assemble the sweep repository from the same config the server reads."""
    from ai.backend.manager.models.base import ensure_all_tables_registered
    from ai.backend.manager.repositories.db.engine import connect_database
    from ai.backend.manager.repositories.ops.v2.secret.provider import SecretOpsProvider
    from ai.backend.manager.repositories.secret.repository import SecretRepository
    from ai.backend.manager.secret.pool import KeyProviderPool

    from .context import config_provider_ctx

    # This standalone CLI process has not imported the full model tree, so register
    # every table before the sweep issues its first query.
    ensure_all_tables_registered()
    bootstrap_config = await cli_ctx.get_bootstrap_config()
    async with (
        connect_database(bootstrap_config.db) as db,
        config_provider_ctx(cli_ctx) as config_provider,
    ):
        pool = KeyProviderPool.from_config(config_provider.config.secret_encryption)
        yield SecretRepository(SecretOpsProvider(db), pool)


@cli.command()
@click.option(
    "--key-id",
    default="v1",
    help="The id the generated key is configured under.",
)
def generate_key(key_id: str) -> None:
    """Generate a key encryption key and print the config section holding it."""
    material = base64.b64encode(secrets.token_bytes(KEY_SIZE)).decode("ascii")
    click.echo("[secret-encryption]")
    click.echo('write-provider-type = "config"')
    click.echo("")
    click.echo("[secret-encryption.config-provider]")
    click.echo(f'active-key-id = "{key_id}"')
    click.echo("")
    click.echo("[secret-encryption.config-provider.keys]")
    click.echo(f'{key_id} = "{material}"')


@cli.command()
@click.pass_obj
def reencrypt_keypairs(cli_ctx: CLIContext) -> None:
    """Encrypt every stored keypair secret again through the write provider."""

    async def _impl() -> None:
        async with _repository_ctx(cli_ctx) as repository:
            progress = await repository.reencrypt_keypair_secrets()
        log.info("Read {} row(s) and wrote {}.", progress.scanned, progress.reencrypted)
        _print_status(progress.status)

    asyncio.run(_impl())


@cli.command()
@click.pass_obj
def status(cli_ctx: CLIContext) -> None:
    """Report the stored keypair secrets per key id."""

    async def _impl() -> None:
        async with _repository_ctx(cli_ctx) as repository:
            swept = await repository.keypair_secret_status()
        _print_status(swept)

    asyncio.run(_impl())


def _print_status(swept: SecretSweepStatus) -> None:
    click.echo(f"write provider: {swept.write_provider_type.value}")
    click.echo(
        tabulate(
            [
                (count.provider_type.value, count.key_id or _ABSENT, count.count)
                for count in swept.counts
            ],
            headers=_STATUS_COLUMNS,
        )
    )
