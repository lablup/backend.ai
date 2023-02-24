import contextlib
import logging
from pprint import pformat, pprint
from typing import AsyncIterator

import sqlalchemy as sa
from redis.asyncio.client import Pipeline, Redis
from tabulate import tabulate

from ai.backend.common import redis_helper
from ai.backend.common.docker import ImageRef
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.exception import UnknownImageReference
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.manager.cli.context import redis_ctx
from ai.backend.manager.models.image import ImageAliasRow, ImageRow
from ai.backend.manager.models.image import rescan_images as rescan_images_func
from ai.backend.manager.models.utils import connect_database

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


@contextlib.asynccontextmanager
async def etcd_ctx(cli_ctx) -> AsyncIterator[AsyncEtcd]:
    local_config = cli_ctx.local_config
    creds = None
    if local_config["etcd"]["user"]:
        creds = {
            "user": local_config["etcd"]["user"],
            "password": local_config["etcd"]["password"],
        }
    scope_prefix_map = {
        ConfigScopes.GLOBAL: "",
        # TODO: provide a way to specify other scope prefixes
    }
    etcd = AsyncEtcd(
        local_config["etcd"]["addr"],
        local_config["etcd"]["namespace"],
        scope_prefix_map,
        credentials=creds,
    )
    try:
        yield etcd
    finally:
        await etcd.close()


async def list_images(cli_ctx, short, installed_only):
    # Connect to postgreSQL DB
    async with (
        connect_database(cli_ctx.local_config) as db,
        db.begin_readonly_session() as session,
        redis_ctx(cli_ctx) as redis_conn_set,
    ):
        displayed_items = []
        try:
            items = await ImageRow.list(session)
            # NOTE: installed/installed_agents fields are no longer provided in CLI,
            #       until we finish the epic refactoring of image metadata db.
            if installed_only:

                async def _build_scard_pipeline(redis: Redis) -> Pipeline:
                    pipe = redis.pipeline()
                    for item in items:
                        await pipe.scard(item.name)
                    return pipe

                installed_counts = await redis_helper.execute(
                    redis_conn_set.image, _build_scard_pipeline
                )
                installed_items = []

                async def _build_smembers_pipeline(redis: Redis) -> Pipeline:
                    pipe = redis.pipeline()
                    for item, installed_count in zip(items, installed_counts):
                        if installed_count > 0:
                            installed_items.append(item)
                            await pipe.smembers(item.name)
                    return pipe

                agents_per_installed_items = await redis_helper.execute(
                    redis_conn_set.image,
                    _build_smembers_pipeline,
                )
                for item, installed_agents in zip(installed_items, agents_per_installed_items):
                    formatted_installed_agents = " ".join(
                        map(lambda s: s.decode(), installed_agents)
                    )
                    if short:
                        displayed_items.append(
                            (
                                item.image_ref.canonical,
                                item.config_digest,
                                formatted_installed_agents,
                            )
                        )
                    else:
                        print(f"{pformat(item)} @ {formatted_installed_agents}")
            else:
                for item in items:
                    if short:
                        displayed_items.append((item.image_ref.canonical, item.config_digest))
                    else:
                        pprint(item)
            if short:
                print(tabulate(displayed_items, tablefmt="plain"))
        except Exception:
            log.exception("An error occurred.")


async def inspect_image(cli_ctx, canonical_or_alias, architecture):
    async with (
        connect_database(cli_ctx.local_config) as db,
        db.begin_readonly_session() as session,
    ):
        try:
            image_row = await ImageRow.resolve(
                session,
                [
                    ImageRef(canonical_or_alias, ["*"], architecture),
                    canonical_or_alias,
                ],
            )
            pprint(await image_row.inspect())
        except UnknownImageReference:
            log.exception("Image not found.")
        except Exception:
            log.exception("An error occurred.")


async def forget_image(cli_ctx, canonical_or_alias, architecture):
    async with (
        connect_database(cli_ctx.local_config) as db,
        db.begin_session() as session,
    ):
        try:
            image_row = await ImageRow.resolve(
                session,
                [
                    ImageRef(canonical_or_alias, ["*"], architecture),
                    canonical_or_alias,
                ],
            )
            await session.delete(image_row)
        except UnknownImageReference:
            log.exception("Image not found.")
        except Exception:
            log.exception("An error occurred.")


async def set_image_resource_limit(
    cli_ctx,
    canonical_or_alias,
    slot_type,
    range_value,
    architecture,
):
    async with (
        connect_database(cli_ctx.local_config) as db,
        db.begin_session() as session,
    ):
        try:
            image_row = await ImageRow.resolve(
                session,
                [
                    ImageRef(canonical_or_alias, ["*"], architecture),
                    canonical_or_alias,
                ],
            )
            await image_row.set_resource_limit(slot_type, range_value)
        except UnknownImageReference:
            log.exception("Image not found.")
        except Exception:
            log.exception("An error occurred.")


async def rescan_images(cli_ctx, registry):
    async with (
        connect_database(cli_ctx.local_config) as db,
        etcd_ctx(cli_ctx) as etcd,
    ):
        try:
            await rescan_images_func(etcd, db, registry=registry)
        except Exception:
            log.exception("An error occurred.")


async def alias(cli_ctx, alias, target, architecture):
    async with (
        connect_database(cli_ctx.local_config) as db,
        db.begin_session() as session,
    ):
        try:
            image_row = await ImageRow.resolve(
                session,
                [
                    ImageRef(target, ["*"], architecture),
                ],
            )
            await ImageAliasRow.create(session, alias, image_row)
        except UnknownImageReference:
            log.exception("Image not found.")
        except Exception:
            log.exception("An error occurred.")


async def dealias(cli_ctx, alias):
    async with (
        connect_database(cli_ctx.local_config) as db,
        db.begin_session() as session,
    ):
        alias_row = await session.scalar(
            sa.select(ImageAliasRow).where(ImageAliasRow.alias == alias),
        )
        if alias_row is None:
            log.exception("Alias not found.")
            return
        await session.delete(alias_row)
