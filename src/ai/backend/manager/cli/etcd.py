from __future__ import annotations

import asyncio
import json
import logging
import sys
from typing import TYPE_CHECKING

import click

from ai.backend.cli.types import ExitCode
from ai.backend.common.cli import EnumChoice, MinMaxRange
from ai.backend.common.etcd import ConfigScopes
from ai.backend.common.etcd import quote as etcd_quote
from ai.backend.common.etcd import unquote as etcd_unquote
from ai.backend.common.logging import BraceStyleAdapter

from .context import etcd_ctx
from .image_impl import alias as alias_impl
from .image_impl import dealias as dealias_impl
from .image_impl import forget_image as forget_image_impl
from .image_impl import inspect_image as inspect_image_impl
from .image_impl import list_images as list_images_impl
from .image_impl import rescan_images as rescan_images_impl
from .image_impl import set_image_resource_limit as set_image_resource_limit_impl

if TYPE_CHECKING:
    from .context import CLIContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.argument("key")
@click.argument("value")
@click.option(
    "-s",
    "--scope",
    type=EnumChoice(ConfigScopes),
    default=ConfigScopes.GLOBAL,
    help="The configuration scope to put the value.",
)
@click.pass_obj
def put(cli_ctx: CLIContext, key, value, scope) -> None:
    """Put a single key-value pair into the etcd."""

    async def _impl():
        async with etcd_ctx(cli_ctx) as etcd:
            try:
                await etcd.put(key, value, scope=scope)
            except Exception:
                log.exception("An error occurred.")

    asyncio.run(_impl())


@cli.command()
@click.argument("key", type=str)
@click.argument("file", type=click.File("rb"))
@click.option(
    "-s",
    "--scope",
    type=EnumChoice(ConfigScopes),
    default=ConfigScopes.GLOBAL,
    help="The configuration scope to put the value.",
)
@click.pass_obj
def put_json(cli_ctx: CLIContext, key, file, scope) -> None:
    """
    Put a JSON object from FILE to the etcd as flattened key-value pairs
    under the given KEY prefix.
    """

    async def _impl():
        async with etcd_ctx(cli_ctx) as etcd:
            try:
                value = json.load(file)
                await etcd.put_prefix(key, value, scope=scope)
            except Exception:
                log.exception("An error occurred.")

    asyncio.run(_impl())


@cli.command()
@click.argument("src_prefix", type=str)
@click.argument("dst_prefix", type=str)
@click.option(
    "-s",
    "--scope",
    type=EnumChoice(ConfigScopes),
    default=ConfigScopes.GLOBAL,
    help=(
        "The configuration scope to get/put the subtree. "
        "To move between different scopes, use the global scope "
        "and specify the per-scope prefixes manually."
    ),
)
@click.pass_obj
def move_subtree(cli_ctx: CLIContext, src_prefix, dst_prefix, scope) -> None:
    """
    Move a subtree to another key prefix.
    """

    async def _impl():
        async with etcd_ctx(cli_ctx) as etcd:
            try:
                subtree = await etcd.get_prefix(src_prefix, scope=scope)
                await etcd.put_prefix(dst_prefix, subtree, scope=scope)
                await etcd.delete_prefix(src_prefix, scope=scope)
            except Exception:
                log.exception("An error occurred.")

    asyncio.run(_impl())


@cli.command()
@click.argument("key")
@click.option(
    "--prefix",
    is_flag=True,
    help="Get all key-value pairs prefixed with the given key as a JSON form.",
)
@click.option(
    "-s",
    "--scope",
    type=EnumChoice(ConfigScopes),
    default=ConfigScopes.GLOBAL,
    help="The configuration scope to put the value.",
)
@click.pass_obj
def get(cli_ctx: CLIContext, key, prefix, scope) -> None:
    """
    Get the value of a key in the configured etcd namespace.
    """

    async def _impl():
        async with etcd_ctx(cli_ctx) as etcd:
            try:
                if prefix:
                    data = await etcd.get_prefix(key, scope=scope)
                    print(json.dumps(dict(data), indent=4))
                else:
                    val = await etcd.get(key, scope=scope)
                    if val is None:
                        sys.exit(ExitCode.FAILURE)
                    print(val)
            except Exception:
                log.exception("An error occurred.")

    asyncio.run(_impl())


@cli.command()
@click.argument("key")
@click.option("--prefix", is_flag=True, help="Delete all keys prefixed with the given key.")
@click.option(
    "-s",
    "--scope",
    type=EnumChoice(ConfigScopes),
    default=ConfigScopes.GLOBAL,
    help="The configuration scope to put the value.",
)
@click.pass_obj
def delete(cli_ctx: CLIContext, key, prefix, scope) -> None:
    """Delete the key in the configured etcd namespace."""

    async def _impl():
        async with etcd_ctx(cli_ctx) as etcd:
            try:
                if prefix:
                    data = await etcd.get_prefix(key, scope=scope)
                    if not data:
                        log.info(f"No keys found to delete with prefix: {key}")
                        return
                    await etcd.delete_prefix(key, scope=scope)
                    log.info(f"All keys starting with '{key}' successfully deleted.")
                else:
                    data = await etcd.get(key, scope=scope)
                    if data is None:
                        log.info(f"No key found to delete: {key}")
                        return
                    await etcd.delete(key, scope=scope)
                log.info(f"Key '{key}' successfully deleted.")
            except Exception:
                log.exception("An error occurred.")

    asyncio.run(_impl())


@cli.command()
@click.option("-s", "--short", is_flag=True, help="Show only the image references and digests.")
@click.option("-i", "--installed", is_flag=True, help="Show only the installed images.")
@click.pass_obj
def list_images(cli_ctx, short, installed) -> None:
    """List all configured images."""
    log.warning("etcd list-images command is deprecated, use image list instead")
    asyncio.run(list_images_impl(cli_ctx, short, installed))


@cli.command()
@click.argument("canonical_or_alias")
@click.argument("architecture")
@click.pass_obj
def inspect_image(cli_ctx, canonical_or_alias, architecture) -> None:
    """Show the details of the given image or alias."""
    log.warning("etcd inspect-image command is deprecated, use image inspect instead")
    asyncio.run(inspect_image_impl(cli_ctx, canonical_or_alias, architecture))


@cli.command()
@click.argument("canonical_or_alias")
@click.argument("architecture")
@click.pass_obj
def forget_image(cli_ctx, canonical_or_alias, architecture) -> None:
    """Forget (delete) a specific image."""
    log.warning("etcd forget-image command is deprecated, use image forget instead")
    asyncio.run(forget_image_impl(cli_ctx, canonical_or_alias, architecture))


@cli.command()
@click.argument("canonical_or_alias")
@click.argument("slot_type")
@click.argument("range_value", type=MinMaxRange)
@click.argument("architecture")
@click.pass_obj
def set_image_resource_limit(
    cli_ctx,
    canonical_or_alias,
    slot_type,
    range_value,
    architecture,
) -> None:
    """Set the MIN:MAX values of a SLOT_TYPE limit for the given image REFERENCE."""
    log.warning(
        "etcd set-image-resource-limit command is deprecated, use image set-resource-limit instead"
    )
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
@click.argument("registry")
@click.pass_obj
def rescan_images(cli_ctx: CLIContext, registry: str) -> None:
    """
    Update the kernel image metadata from all configured docker registries.

    Pass the name (usually hostname or "lablup") of the Docker registry configured as REGISTRY.
    """
    log.warning("etcd rescan-images command is deprecated, use image rescan instead")
    asyncio.run(rescan_images_impl(cli_ctx, registry, False))


@cli.command()
@click.argument("alias")
@click.argument("target")
@click.argument("architecture")
@click.pass_obj
def alias(cli_ctx: CLIContext, alias: str, target: str, architecture: str) -> None:
    """Add an image alias from the given alias to the target image reference."""
    log.warning("etcd alias command is deprecated, use image alias instead")
    asyncio.run(alias_impl(cli_ctx, alias, target, architecture))


@cli.command()
@click.argument("alias")
@click.pass_obj
def dealias(cli_ctx: CLIContext, alias: str) -> None:
    """Remove an alias."""
    log.warning("etcd dealias command is deprecated, use image dealias instead")
    asyncio.run(dealias_impl(cli_ctx, alias))


@cli.command()
@click.argument("value")
@click.pass_obj
def quote(cli_ctx: CLIContext, value: str) -> None:
    """
    Quote the given string for use as a URL piece in etcd keys.
    Use this to generate argument inputs for aliases and raw image keys.
    """
    print(etcd_quote(value))


@cli.command()
@click.argument("value")
@click.pass_obj
def unquote(cli_ctx: CLIContext, value: str) -> None:
    """
    Unquote the given string used as a URL piece in etcd keys.
    """
    print(etcd_unquote(value))


@cli.command()
@click.argument("proxy")
@click.argument("scaling_groups")
@click.option(
    "-s",
    "--scope",
    type=EnumChoice(ConfigScopes),
    default=ConfigScopes.GLOBAL,
    help="The configuration scope to put the value.",
)
@click.pass_obj
def set_storage_sftp_scaling_group(
    cli_ctx: CLIContext,
    proxy: str,
    scaling_groups: str,
    scope: ConfigScopes,
) -> None:
    """
    Updates storage proxy node config's SFTP desginated scaling groups.
    To enter multiple scaling groups concatenate names with comma(,).
    """

    async def _impl():
        async with etcd_ctx(cli_ctx) as etcd:
            data = await etcd.get_prefix(f"volumes/proxies/{proxy}", scope=scope)
            if len(data) == 0:
                log.error("proxy {} does not exist", proxy)
                sys.exit(ExitCode.FAILURE)
            await etcd.put(
                f"volumes/proxies/{proxy}/sftp_scaling_groups",
                ",".join([x.strip() for x in scaling_groups.split(",")]),
            )

    asyncio.run(_impl())


@cli.command()
@click.argument("proxy")
@click.option(
    "-s",
    "--scope",
    type=EnumChoice(ConfigScopes),
    default=ConfigScopes.GLOBAL,
    help="The configuration scope to put the value.",
)
@click.pass_obj
def remove_storage_sftp_scaling_group(
    cli_ctx: CLIContext,
    proxy: str,
    scope: ConfigScopes,
) -> None:
    """
    Removes storage proxy node config's SFTP desginated scaling groups.
    """

    async def _impl():
        async with etcd_ctx(cli_ctx) as etcd:
            data = await etcd.get_prefix(f"volumes/proxies/{proxy}", scope=scope)
            if len(data) == 0:
                log.error("proxy {} does not exist", proxy)
                sys.exit(ExitCode.FAILURE)
            await etcd.delete(f"volumes/proxies/{proxy}/sftp_scaling_groups")

    asyncio.run(_impl())
