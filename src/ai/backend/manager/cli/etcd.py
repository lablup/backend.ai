from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from typing import AsyncIterator, TYPE_CHECKING
import sys

import click

from ai.backend.common.cli import EnumChoice, MinMaxRange
from ai.backend.common.config import redis_config_iv
from ai.backend.common.etcd import (
    AsyncEtcd, ConfigScopes,
    quote as etcd_quote,
    unquote as etcd_unquote,
)
from ai.backend.common.logging import BraceStyleAdapter

from .image_impl import (
    alias as alias_impl,
    dealias as dealias_impl,
    forget_image as forget_image_impl,
    inspect_image as inspect_image_impl,
    list_images as list_images_impl,
    rescan_images as rescan_images_impl,
    set_image_resource_limit as set_image_resource_limit_impl,
)
from ..config import SharedConfig

if TYPE_CHECKING:
    from .context import CLIContext

log = BraceStyleAdapter(logging.getLogger(__name__))


@click.group()
def cli() -> None:
    pass


@contextlib.asynccontextmanager
async def etcd_ctx(cli_ctx: CLIContext) -> AsyncIterator[AsyncEtcd]:
    local_config = cli_ctx.local_config
    creds = None
    if local_config['etcd']['user']:
        creds = {
            'user': local_config['etcd']['user'],
            'password': local_config['etcd']['password'],
        }
    scope_prefix_map = {
        ConfigScopes.GLOBAL: '',
        # TODO: provide a way to specify other scope prefixes
    }
    etcd = AsyncEtcd(local_config['etcd']['addr'], local_config['etcd']['namespace'],
                     scope_prefix_map, credentials=creds)
    try:
        yield etcd
    finally:
        await etcd.close()


@contextlib.asynccontextmanager
async def config_ctx(cli_ctx: CLIContext) -> AsyncIterator[SharedConfig]:
    local_config = cli_ctx.local_config
    # scope_prefix_map is created inside ConfigServer
    shared_config = SharedConfig(
        local_config['etcd']['addr'],
        local_config['etcd']['user'],
        local_config['etcd']['password'],
        local_config['etcd']['namespace'],
    )
    await shared_config.reload()
    raw_redis_config = await shared_config.etcd.get_prefix('config/redis')
    local_config['redis'] = redis_config_iv.check(raw_redis_config)
    try:
        yield shared_config
    finally:
        await shared_config.close()


@cli.command()
@click.argument('key')
@click.argument('value')
@click.option('-s', '--scope', type=EnumChoice(ConfigScopes), default=ConfigScopes.GLOBAL,
              help='The configuration scope to put the value.')
@click.pass_obj
def put(cli_ctx: CLIContext, key, value, scope) -> None:
    '''Put a single key-value pair into the etcd.'''
    async def _impl():
        async with etcd_ctx(cli_ctx) as etcd:
            try:
                await etcd.put(key, value, scope=scope)
            except Exception:
                log.exception('An error occurred.')
    with cli_ctx.logger:
        asyncio.run(_impl())


@cli.command()
@click.argument('key', type=str)
@click.argument('file', type=click.File('rb'))
@click.option('-s', '--scope', type=EnumChoice(ConfigScopes),
              default=ConfigScopes.GLOBAL,
              help='The configuration scope to put the value.')
@click.pass_obj
def put_json(cli_ctx: CLIContext, key, file, scope) -> None:
    '''
    Put a JSON object from FILE to the etcd as flattened key-value pairs
    under the given KEY prefix.
    '''
    async def _impl():
        async with etcd_ctx(cli_ctx) as etcd:
            try:
                value = json.load(file)
                await etcd.put_prefix(key, value, scope=scope)
            except Exception:
                log.exception('An error occurred.')
    with cli_ctx.logger:
        asyncio.run(_impl())


@cli.command()
@click.argument('src_prefix', type=str)
@click.argument('dst_prefix', type=str)
@click.option('-s', '--scope', type=EnumChoice(ConfigScopes),
              default=ConfigScopes.GLOBAL,
              help='The configuration scope to get/put the subtree. '
                   'To move between different scopes, use the global scope '
                   'and specify the per-scope prefixes manually.')
@click.pass_obj
def move_subtree(cli_ctx: CLIContext, src_prefix, dst_prefix, scope) -> None:
    '''
    Move a subtree to another key prefix.
    '''
    async def _impl():
        async with etcd_ctx(cli_ctx) as etcd:
            try:
                subtree = await etcd.get_prefix(src_prefix, scope=scope)
                await etcd.put_prefix(dst_prefix, subtree, scope=scope)
                await etcd.delete_prefix(src_prefix, scope=scope)
            except Exception:
                log.exception('An error occurred.')
    with cli_ctx.logger:
        asyncio.run(_impl())


@cli.command()
@click.argument('key')
@click.option('--prefix', is_flag=True,
              help='Get all key-value pairs prefixed with the given key '
                   'as a JSON form.')
@click.option('-s', '--scope', type=EnumChoice(ConfigScopes),
              default=ConfigScopes.GLOBAL,
              help='The configuration scope to put the value.')
@click.pass_obj
def get(cli_ctx: CLIContext, key, prefix, scope) -> None:
    '''
    Get the value of a key in the configured etcd namespace.
    '''
    async def _impl():
        async with etcd_ctx(cli_ctx) as etcd:
            try:
                if prefix:
                    data = await etcd.get_prefix(key, scope=scope)
                    print(json.dumps(dict(data), indent=4))
                else:
                    val = await etcd.get(key, scope=scope)
                    if val is None:
                        sys.exit(1)
                    print(val)
            except Exception:
                log.exception('An error occurred.')
    with cli_ctx.logger:
        asyncio.run(_impl())


@cli.command()
@click.argument('key')
@click.option('--prefix', is_flag=True,
              help='Delete all keys prefixed with the given key.')
@click.option('-s', '--scope', type=EnumChoice(ConfigScopes),
              default=ConfigScopes.GLOBAL,
              help='The configuration scope to put the value.')
@click.pass_obj
def delete(cli_ctx: CLIContext, key, prefix, scope) -> None:
    '''Delete the key in the configured etcd namespace.'''
    async def _impl():
        async with etcd_ctx(cli_ctx) as etcd:
            try:
                if prefix:
                    await etcd.delete_prefix(key, scope=scope)
                else:
                    await etcd.delete(key, scope=scope)
            except Exception:
                log.exception('An error occurred.')
    with cli_ctx.logger:
        asyncio.run(_impl())


@cli.command()
@click.option('-s', '--short', is_flag=True,
              help='Show only the image references and digests.')
@click.option('-i', '--installed', is_flag=True,
              help='Show only the installed images.')
@click.pass_obj
def list_images(cli_ctx, short, installed) -> None:
    '''List all configured images.'''
    with cli_ctx.logger:
        log.warn('etcd list-images command is deprecated, use image list instead')
        asyncio.run(list_images_impl(cli_ctx, short, installed))


@cli.command()
@click.argument('canonical_or_alias')
@click.argument('architecture')
@click.pass_obj
def inspect_image(cli_ctx, canonical_or_alias, architecture) -> None:
    '''Show the details of the given image or alias.'''
    with cli_ctx.logger:
        log.warn('etcd inspect-image command is deprecated, use image inspect instead')
        asyncio.run(inspect_image_impl(cli_ctx, canonical_or_alias, architecture))


@cli.command()
@click.argument('canonical_or_alias')
@click.argument('architecture')
@click.pass_obj
def forget_image(cli_ctx, canonical_or_alias, architecture) -> None:
    '''Forget (delete) a specific image.'''
    with cli_ctx.logger:
        log.warn('etcd forget-image command is deprecated, use image forget instead')
        asyncio.run(forget_image_impl(cli_ctx, canonical_or_alias, architecture))


@cli.command()
@click.argument('canonical_or_alias')
@click.argument('slot_type')
@click.argument('range_value', type=MinMaxRange)
@click.argument('architecture')
@click.pass_obj
def set_image_resource_limit(
    cli_ctx,
    canonical_or_alias,
    slot_type,
    range_value,
    architecture,
) -> None:
    '''Set the MIN:MAX values of a SLOT_TYPE limit for the given image REFERENCE.'''
    with cli_ctx.logger:
        log.warn('etcd set-image-resource-limit command is deprecated, '
                 'use image set-resource-limit instead')
        asyncio.run(set_image_resource_limit_impl(
            cli_ctx,
            canonical_or_alias,
            slot_type,
            range_value,
            architecture,
        ))


@cli.command()
@click.argument('registry')
@click.pass_obj
def rescan_images(cli_ctx: CLIContext, registry) -> None:
    '''
    Update the kernel image metadata from all configured docker registries.

    Pass the name (usually hostname or "lablup") of the Docker registry configured as REGISTRY.
    '''
    with cli_ctx.logger:
        log.warn('etcd rescan-images command is deprecated, use image rescan instead')
        asyncio.run(rescan_images_impl(cli_ctx, registry))


@cli.command()
@click.argument('alias')
@click.argument('target')
@click.argument('architecture')
@click.pass_obj
def alias(cli_ctx, alias, target, architecture) -> None:
    '''Add an image alias from the given alias to the target image reference.'''
    with cli_ctx.logger:
        log.warn('etcd alias command is deprecated, use image alias instead')
        asyncio.run(alias_impl(cli_ctx, alias, target, architecture))


@cli.command()
@click.argument('alias')
@click.pass_obj
def dealias(cli_ctx, alias) -> None:
    '''Remove an alias.'''
    with cli_ctx.logger:
        log.warn('etcd dealias command is deprecated, use image dealias instead')
        asyncio.run(dealias_impl(cli_ctx, alias))


@cli.command()
@click.argument('value')
@click.pass_obj
def quote(cli_ctx: CLIContext, value) -> None:
    '''
    Quote the given string for use as a URL piece in etcd keys.
    Use this to generate argument inputs for aliases and raw image keys.
    '''
    print(etcd_quote(value))


@cli.command()
@click.argument('value')
@click.pass_obj
def unquote(cli_ctx: CLIContext, value) -> None:
    '''
    Unquote the given string used as a URL piece in etcd keys.
    '''
    print(etcd_unquote(value))
