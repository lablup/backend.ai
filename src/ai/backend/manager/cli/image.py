from __future__ import annotations

import asyncio
import logging
from typing import Optional

import click

from ai.backend.common.cli import MinMaxRange
from ai.backend.common.logging import BraceStyleAdapter

from .context import CLIContext
from .image_impl import alias as alias_impl
from .image_impl import dealias as dealias_impl
from .image_impl import forget_image as forget_image_impl
from .image_impl import inspect_image as inspect_image_impl
from .image_impl import list_images as list_images_impl
from .image_impl import rescan_images as rescan_images_impl
from .image_impl import set_image_resource_limit as set_image_resource_limit_impl
from .image_impl import validate_image_alias as validate_image_alias_impl
from .image_impl import validate_image_canonical as validate_image_canonical_impl

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@click.group()
def cli() -> None:
    pass


@cli.command(name="list")
@click.option("-s", "--short", is_flag=True, help="Show only the image references and digests.")
@click.option("-i", "--installed", is_flag=True, help="Show only the installed images.")
@click.pass_obj
def list_images(cli_ctx, short, installed) -> None:
    """List all configured images."""
    asyncio.run(list_images_impl(cli_ctx, short, installed))


@cli.command()
@click.argument("canonical_or_alias")
@click.argument("architecture")
@click.pass_obj
def inspect(cli_ctx, canonical_or_alias, architecture) -> None:
    """Show the details of the given image or alias."""
    asyncio.run(inspect_image_impl(cli_ctx, canonical_or_alias, architecture))


@cli.command()
@click.argument("canonical_or_alias")
@click.argument("architecture")
@click.pass_obj
def forget(cli_ctx, canonical_or_alias, architecture) -> None:
    """Forget (delete) a specific image."""
    asyncio.run(forget_image_impl(cli_ctx, canonical_or_alias, architecture))


@cli.command()
@click.argument("canonical_or_alias")
@click.argument("slot_type")
@click.argument("range_value", type=MinMaxRange)
@click.argument("architecture")
@click.pass_obj
def set_resource_limit(
    cli_ctx,
    canonical_or_alias,
    slot_type,
    range_value,
    architecture,
) -> None:
    """Set the MIN:MAX values of a SLOT_TYPE limit for the given image REFERENCE."""
    asyncio.run(
        set_image_resource_limit_impl(
            cli_ctx,
            canonical_or_alias,
            slot_type,
            range_value,
            architecture,
        )
    )


@cli.command()
@click.argument("registry_or_image", required=False, default="")
@click.option(
    "--local",
    is_flag=True,
    default=False,
    help="Scan the local Docker daemon instead of a registry",
)
@click.pass_obj
def rescan(cli_ctx, registry_or_image: str, local: bool) -> None:
    """
    Update the kernel image metadata from all configured docker registries.

    Pass the name (usually hostname or "lablup") of the Docker registry configured as REGISTRY.
    """
    asyncio.run(rescan_images_impl(cli_ctx, registry_or_image, local))


@cli.command()
@click.argument("alias")
@click.argument("target")
@click.argument("architecture")
@click.pass_obj
def alias(cli_ctx, alias, target, architecture) -> None:
    """Add an image alias from the given alias to the target image reference."""
    asyncio.run(alias_impl(cli_ctx, alias, target, architecture))


@cli.command()
@click.argument("alias")
@click.pass_obj
def dealias(cli_ctx, alias) -> None:
    """Remove an alias."""
    asyncio.run(dealias_impl(cli_ctx, alias))


@cli.command()
@click.argument("alias")
@click.pass_obj
def validate_image_alias(cli_ctx: CLIContext, alias: str) -> None:
    """Validate a local/remote image's labels and platform tag formats by image alias."""
    asyncio.run(validate_image_alias_impl(cli_ctx, alias))


@cli.command()
@click.argument("canonical")
@click.option(
    "--arch",
    "-a",
    type=str,
    help="Specify architecture, Can't use with --current option",
)
@click.option(
    "--current",
    "-c",
    is_flag=True,
    default=False,
    help="Use default architecture as the current client's architecture",
)
@click.pass_obj
def validate_image_canonical(
    cli_ctx: CLIContext, canonical: str, current: bool, arch: Optional[str] = None
) -> None:
    """
    Validate a local/remote image's labels and platform tag formats by image canonical.

    Write in the format registry/name:tag
    """
    if arch and current:
        raise click.UsageError("Cannot use both --architecture and --current together")
    asyncio.run(validate_image_canonical_impl(cli_ctx, canonical, current, arch))
