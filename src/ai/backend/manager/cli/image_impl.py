from __future__ import annotations

import logging
from pprint import pformat, pprint
from typing import Any, Optional

import click
import sqlalchemy as sa
from tabulate import tabulate

from ai.backend.common.arch import CURRENT_ARCH
from ai.backend.common.docker import validate_image_labels
from ai.backend.common.exception import UnknownImageReference
from ai.backend.common.types import ImageAlias
from ai.backend.logging import BraceStyleAdapter

from ..data.image.types import ImageStatus
from ..models.image import ImageAliasRow, ImageIdentifier, ImageRow
from ..models.image import rescan_images as rescan_images_func
from ..models.utils import connect_database
from .context import CLIContext, redis_ctx

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


async def list_images(cli_ctx: CLIContext, short, installed_only):
    # Connect to postgreSQL DB
    bootstrap_config = await cli_ctx.get_bootstrap_config()
    async with (
        connect_database(bootstrap_config.db) as db,
        db.begin_readonly_session() as session,
        redis_ctx(cli_ctx) as redis_conn_set,
    ):
        displayed_items: list[tuple[Any, ...]] = []
        try:
            # Idea: Add `--include-deleted` option to include deleted images?
            items = await ImageRow.list(session)
            # NOTE: installed/installed_agents fields are no longer provided in CLI,
            #       until we finish the epic refactoring of image metadata db.
            if installed_only:
                image_canonicals = [item.name for item in items]
                installed_counts = await redis_conn_set.image.get_agent_counts_for_images(
                    image_canonicals
                )
                installed_items = []

                for item, installed_count in zip(items, installed_counts):
                    if installed_count > 0:
                        installed_items.append(item)

                installed_canonicals = [item.name for item in installed_items]
                agents_per_installed_items = await redis_conn_set.image.get_agents_for_images(
                    installed_canonicals
                )

                for item, installed_agents in zip(installed_items, agents_per_installed_items):
                    formatted_installed_agents = " ".join(installed_agents)
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
        except Exception as e:
            log.exception(f"An error occurred. Error: {e}")


async def inspect_image(cli_ctx: CLIContext, canonical_or_alias, architecture):
    bootstrap_config = await cli_ctx.get_bootstrap_config()
    async with (
        connect_database(bootstrap_config.db) as db,
        db.begin_readonly_session() as session,
    ):
        try:
            image_row = await ImageRow.resolve(
                session,
                [
                    ImageIdentifier(canonical_or_alias, architecture),
                    ImageAlias(canonical_or_alias),
                ],
            )
            pprint(await image_row.inspect())
        except UnknownImageReference:
            log.exception("Image not found.")
        except Exception as e:
            log.exception(f"An error occurred. Error: {e}")


async def forget_image(cli_ctx, canonical_or_alias, architecture):
    async with (
        connect_database(cli_ctx.bootstrap_config.db) as db,
        db.begin_session() as session,
    ):
        try:
            image_row = await ImageRow.resolve(
                session,
                [
                    ImageIdentifier(canonical_or_alias, architecture),
                    ImageAlias(canonical_or_alias),
                ],
            )
            await image_row.mark_as_deleted(session)
        except UnknownImageReference:
            log.exception("Image not found.")
        except Exception as e:
            log.exception(f"An error occurred. Error: {e}")


async def purge_image(
    cli_ctx: CLIContext, canonical_or_alias: str, architecture: str, remove_from_registry: bool
):
    bootstrap_config = await cli_ctx.get_bootstrap_config()
    async with (
        connect_database(bootstrap_config.db) as db,
        db.begin_session() as session,
    ):
        try:
            image_row = await ImageRow.resolve(
                session,
                [
                    ImageIdentifier(canonical_or_alias, architecture),
                    ImageAlias(canonical_or_alias),
                ],
                filter_by_statuses=None,
            )
            await session.delete(image_row)

            if remove_from_registry:
                await image_row.untag_image_from_registry(db=db, session=session)

        except UnknownImageReference:
            log.exception("Image not found.")
        except Exception as e:
            log.exception(f"An error occurred. Error: {e}")


async def set_image_resource_limit(
    cli_ctx: CLIContext,
    canonical_or_alias,
    slot_type,
    range_value,
    architecture,
):
    bootstrap_config = await cli_ctx.get_bootstrap_config()
    async with (
        connect_database(bootstrap_config.db) as db,
        db.begin_session() as session,
    ):
        try:
            image_row = await ImageRow.resolve(
                session,
                [
                    ImageIdentifier(canonical_or_alias, architecture),
                    ImageAlias(canonical_or_alias),
                ],
            )
            await image_row.set_resource_limit(slot_type, range_value)
        except UnknownImageReference:
            log.exception("Image not found.")
        except Exception as e:
            log.exception(f"An error occurred. Error: {e}")


async def rescan_images(
    cli_ctx: CLIContext, registry_or_image: str, project: Optional[str] = None
) -> None:
    if not registry_or_image:
        raise click.BadArgumentUsage("Please specify a valid registry or full image name.")
    bootstrap_config = await cli_ctx.get_bootstrap_config()
    async with (
        connect_database(bootstrap_config.db) as db,
    ):
        try:
            result = await rescan_images_func(db, registry_or_image, project)
            for error in result.errors:
                log.error(f"Failed to scan registries: {error}")
        except Exception as e:
            log.exception(f"Unknown error occurred. Error: {e}")


async def alias(cli_ctx: CLIContext, alias, target, architecture):
    bootstrap_config = await cli_ctx.get_bootstrap_config()
    async with (
        connect_database(bootstrap_config.db) as db,
        db.begin_session() as session,
    ):
        try:
            image_row = await ImageRow.resolve(
                session,
                [
                    ImageIdentifier(target, architecture),
                ],
            )
            await ImageAliasRow.create(session, alias, image_row)
        except UnknownImageReference:
            log.exception("Image not found.")
        except Exception as e:
            log.exception(f"An error occurred. Error: {e}")


async def dealias(cli_ctx: CLIContext, alias):
    bootstrap_config = await cli_ctx.get_bootstrap_config()
    async with (
        connect_database(bootstrap_config.db) as db,
        db.begin_session() as session,
    ):
        alias_row = await session.scalar(
            sa.select(ImageAliasRow).where(ImageAliasRow.alias == alias),
        )
        if alias_row is None:
            log.exception("Alias not found.")
            return
        await session.delete(alias_row)


async def validate_image_alias(cli_ctx: CLIContext, alias: str) -> None:
    bootstrap_config = await cli_ctx.get_bootstrap_config()
    async with (
        connect_database(bootstrap_config.db) as db,
        db.begin_readonly_session() as session,
    ):
        try:
            image_row = await ImageRow.from_alias(session, alias)
            for key, value in validate_image_labels(image_row.labels).items():
                print(f"{key:<40}: ", end="")
                if isinstance(value, list):
                    value = f"[{', '.join(value)}]"
                print(value)

        except UnknownImageReference:
            log.error(f"No images were found with alias: {alias}")
        except Exception as e:
            log.exception(f"An error occurred. Error: {e}")


def _resolve_architecture(current: bool, architecture: Optional[str]) -> str:
    if architecture is not None:
        return architecture
    if current:
        return CURRENT_ARCH

    raise ValueError("Unreachable code!")


async def validate_image_canonical(
    cli_ctx: CLIContext, canonical: str, current: bool, architecture: Optional[str] = None
) -> None:
    bootstrap_config = await cli_ctx.get_bootstrap_config()
    async with (
        connect_database(bootstrap_config.db) as db,
        db.begin_readonly_session() as session,
    ):
        try:
            if current or architecture is not None:
                resolved_arch = _resolve_architecture(current, architecture)
                image_row = await ImageRow.resolve(
                    session, [ImageIdentifier(canonical, resolved_arch)]
                )

                print(f"{'architecture':<40}: {resolved_arch}")
                for key, value in validate_image_labels(image_row.labels).items():
                    print(f"{key:<40}: ", end="")
                    if isinstance(value, list):
                        value = f"{', '.join(value)}"
                    print(value)
            else:
                rows = await session.scalars(
                    sa.select(ImageRow).where(
                        sa.and_(ImageRow.name == canonical, ImageRow.status == ImageStatus.ALIVE)
                    )
                )
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
                            value = f"{', '.join(value)}"
                        print(value)

        except UnknownImageReference as e:
            log.error(f"{e}")
        except Exception as e:
            log.exception(f"An error occurred. Error: {e}")
