from __future__ import annotations

import logging
from pprint import pformat, pprint
from typing import Optional

import click
import sqlalchemy as sa
from redis.asyncio.client import Pipeline, Redis
from tabulate import tabulate

from ai.backend.common import redis_helper
from ai.backend.common.arch import CURRENT_ARCH
from ai.backend.common.docker import ImageRef, validate_image_labels
from ai.backend.common.exception import UnknownImageReference
from ai.backend.common.logging import BraceStyleAdapter

from ..models.image import ImageAliasRow, ImageRow
from ..models.image import rescan_images as rescan_images_func
from ..models.utils import connect_database
from .context import CLIContext, etcd_ctx, redis_ctx

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


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
                        displayed_items.append((
                            item.image_ref.canonical,
                            item.config_digest,
                            formatted_installed_agents,
                        ))
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


async def rescan_images(cli_ctx: CLIContext, registry_or_image: str, local: bool) -> None:
    if not registry_or_image and not local:
        raise click.BadArgumentUsage("Please specify a valid registry or full image name.")
    async with (
        connect_database(cli_ctx.local_config) as db,
        etcd_ctx(cli_ctx) as etcd,
    ):
        try:
            await rescan_images_func(etcd, db, registry_or_image, local=local)
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


async def validate_image_alias(cli_ctx, alias: str) -> None:
    async with (
        connect_database(cli_ctx.local_config) as db,
        db.begin_readonly_session() as session,
    ):
        try:
            image_row = await ImageRow.from_alias(session, alias)
            for key, value in validate_image_labels(image_row.labels).items():
                print(f"{key:<40}: ", end="")
                if isinstance(value, list):
                    value = f'[{", ".join(value)}]'
                print(value)

        except UnknownImageReference:
            log.error(f"No images were found with alias: {alias}")
        except Exception:
            log.exception("An error occurred.")


async def validate_image_canonical(
    cli_ctx, canonical: str, current: bool, architecture: Optional[str] = None
) -> None:
    async with (
        connect_database(cli_ctx.local_config) as db,
        db.begin_readonly_session() as session,
    ):
        try:
            if current or architecture is not None:
                if current:
                    architecture = architecture or CURRENT_ARCH
                image_row = await session.scalar(
                    sa.select(ImageRow).where(
                        (ImageRow.name == canonical) & (ImageRow.architecture == architecture)
                    )
                )
                if image_row is None:
                    raise UnknownImageReference(f"{canonical}/{architecture}")
                for key, value in validate_image_labels(image_row.labels).items():
                    print(f"{key:<40}: ", end="")
                    if isinstance(value, list):
                        value = f'{", ".join(value)}'
                    print(value)
            else:
                rows = await session.scalars(sa.select(ImageRow).where(ImageRow.name == canonical))
                image_rows = rows.fetchall()
                if not image_rows:
                    raise UnknownImageReference(f"{canonical}")
                for i, image_row in enumerate(image_rows):
                    if i > 0:
                        print("-" * 50)
                    print(f"{'architecture':<40}: {image_row.architecture}")
                    for key, value in validate_image_labels(image_row.labels).items():
                        print(f"{key:<40}: ", end="")
                        if isinstance(value, list):
                            value = f'{", ".join(value)}'
                        print(value)

        except UnknownImageReference as e:
            log.error(f"{e}")
        except Exception:
            log.exception("An error occurred.")
