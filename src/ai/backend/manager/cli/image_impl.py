import contextlib
import logging
from pprint import pprint

import sqlalchemy as sa
from tabulate import tabulate
from typing import AsyncIterator

from ai.backend.common.docker import ImageRef
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.exception import UnknownImageReference
from ai.backend.common.logging import BraceStyleAdapter

from ai.backend.manager.models.image import (
    ImageAliasRow,
    ImageRow,
    rescan_images as rescan_images_func,
)
from ai.backend.manager.models.utils import (
    connect_database,
)

log = BraceStyleAdapter(logging.getLogger(__name__))


@contextlib.asynccontextmanager
async def etcd_ctx(cli_ctx) -> AsyncIterator[AsyncEtcd]:
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


async def list_images(cli_ctx, short, installed):
    async with connect_database(cli_ctx.local_config) as db:
        async with db.begin_readonly_session() as session:
            displayed_items = []
            try:
                items = await ImageRow.list(session)
                # NOTE: installed/installed_agents fields are no longer provided in CLI,
                #       until we finish the epic refactoring of image metadata db.
                for item in items:
                    if installed and not item.installed:
                        continue
                    if short:
                        displayed_items.append((item.image_ref.canonical, item.config_digest))
                    else:
                        pprint(item)
                if short:
                    print(tabulate(displayed_items, tablefmt='plain'))
            except Exception:
                log.exception('An error occurred.')


async def inspect_image(cli_ctx, canonical_or_alias, architecture):
    async with connect_database(cli_ctx.local_config) as db:
        async with db.begin_readonly_session() as session:
            try:
                image_row = await ImageRow.resolve(session, [
                    ImageRef(canonical_or_alias, ['*'], architecture),
                    canonical_or_alias,
                ])
                pprint(await image_row.inspect())
            except UnknownImageReference:
                log.exception('Image not found.')
            except Exception:
                log.exception('An error occurred.')


async def forget_image(cli_ctx, canonical_or_alias, architecture):
    async with connect_database(cli_ctx.local_config) as db:
        async with db.begin_session() as session:
            try:
                image_row = await ImageRow.resolve(session, [
                    ImageRef(canonical_or_alias, ['*'], architecture),
                    canonical_or_alias,
                ])
                await session.delete(image_row)
            except UnknownImageReference:
                log.exception('Image not found.')
            except Exception:
                log.exception('An error occurred.')


async def set_image_resource_limit(
    cli_ctx,
    canonical_or_alias,
    slot_type,
    range_value,
    architecture,
):
    async with connect_database(cli_ctx.local_config) as db:
        async with db.begin_session() as session:
            try:
                image_row = await ImageRow.resolve(session, [
                    ImageRef(canonical_or_alias, ['*'], architecture),
                    canonical_or_alias,
                ])
                await image_row.set_resource_limit(slot_type, range_value)
            except UnknownImageReference:
                log.exception('Image not found.')
            except Exception:
                log.exception('An error occurred.')


async def rescan_images(cli_ctx, registry):
    async with connect_database(cli_ctx.local_config) as db:
        async with etcd_ctx(cli_ctx) as etcd:
            try:
                await rescan_images_func(etcd, db, registry=registry)
            except Exception:
                log.exception('An error occurred.')


async def alias(cli_ctx, alias, target, architecture):
    async with connect_database(cli_ctx.local_config) as db:
        async with db.begin_session() as session:
            try:
                image_row = await ImageRow.resolve(session, [
                    ImageRef(target, ['*'], architecture),
                ])
                await ImageAliasRow.create(session, alias, image_row)
            except UnknownImageReference:
                log.exception('Image not found.')
            except Exception:
                log.exception('An error occurred.')


async def dealias(cli_ctx, alias):
    async with connect_database(cli_ctx.local_config) as db:
        async with db.begin_session() as session:
            alias_row = await session.scalar(
                sa.select(ImageAliasRow)
                .where(ImageAliasRow.alias == alias),
            )
            if alias_row is None:
                log.exception('Alias not found.')
                return
            await session.delete(alias_row)
