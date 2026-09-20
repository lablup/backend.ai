from __future__ import annotations

import logging
from decimal import Decimal
from pprint import pprint
from typing import Any

import click
import sqlalchemy as sa
from sqlalchemy.orm import selectinload
from tabulate import tabulate

from ai.backend.common.arch import CURRENT_ARCH
from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.docker import validate_image_labels
from ai.backend.common.exception import UnknownImageReference
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.container_registry.harbor import HarborRegistry_v2
from ai.backend.manager.data.image.types import ImageData, ImageStatus
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.image import ImageAliasRow, ImageRow
from ai.backend.manager.models.image.purgers import ImagePurger
from ai.backend.manager.models.image.searchable_fields import ImageSearchableFields
from ai.backend.manager.models.image.searchers import (
    AliasedImageSearcher,
    CanonicalImageSearcher,
    ImageSearcher,
    ReferenceImageSearcher,
)
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.db.engine import connect_database
from ai.backend.manager.repositories.image.db_source.db_source import ImageDBSource
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider

from .context import CLIContext, redis_ctx

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


def _register_image_cli_orm_cluster() -> None:
    """Register ORM rows reachable only via string relationships so the CLI can configure mappers (kept minimal, not all models)."""
    from ai.backend.manager.models.agent.row import AgentRow
    from ai.backend.manager.models.resource_group.row import ResourceGroupForProjectRow

    _ = (AgentRow, ResourceGroupForProjectRow)


def _canonical_searcher(canonical: str, architecture: str) -> ImageSearcher:
    return CanonicalImageSearcher(canonical, architecture, [ImageStatus.ALIVE])


def _reference_searcher(reference: str, architecture: str) -> ImageSearcher:
    return ReferenceImageSearcher(reference, architecture, [ImageStatus.ALIVE])


async def _first_image(
    db: ExtendedAsyncSAEngine, searcher: ImageSearcher, reference: str
) -> ImageData:
    async with V2DBOpsProvider(db).read_ops() as r:
        result = await r.search_in_global(searcher)
    if not result.items:
        raise UnknownImageReference(reference)
    return result.items[0]


def _describe(image: ImageData) -> str:
    return f"{image.image_ref.canonical} ({image.image_ref.architecture})"


async def list_images(cli_ctx: CLIContext, short: bool, installed_only: bool) -> None:
    _register_image_cli_orm_cluster()
    # Connect to postgreSQL DB
    bootstrap_config = await cli_ctx.get_bootstrap_config()
    async with (
        connect_database(bootstrap_config.db) as db,
        redis_ctx(cli_ctx) as redis_conn_set,
    ):
        displayed_items: list[tuple[Any, ...]] = []
        try:
            # Idea: Add `--include-deleted` option to include deleted images?
            async with V2DBOpsProvider(db).read_ops() as r:
                result = await r.search_in_global(
                    ImageSearcher(
                        pagination=NoPagination(),
                        conditions=[
                            ImageSearchableFields.own.status.filter.in_([ImageStatus.ALIVE])
                        ],
                    )
                )
            items = result.items
            # NOTE: installed/installed_agents fields are no longer provided in CLI,
            #       until we finish the epic refactoring of image metadata db.
            if installed_only:
                image_ids = [item.id for item in items]
                installed_counts = await redis_conn_set.image.get_agent_counts_for_images(image_ids)
                installed_items: list[ImageData] = []

                for item, installed_count in zip(items, installed_counts, strict=True):
                    if installed_count > 0:
                        installed_items.append(item)

                installed_image_ids = [item.id for item in installed_items]
                agents_per_installed_items = await redis_conn_set.image.get_agents_for_images(
                    installed_image_ids
                )

                for item, installed_agents in zip(
                    installed_items, agents_per_installed_items.values(), strict=True
                ):
                    formatted_installed_agents = " ".join(str(installed_agents))
                    if short:
                        displayed_items.append((
                            item.image_ref.canonical,
                            item.config_digest,
                            formatted_installed_agents,
                        ))
                    else:
                        print(f"{_describe(item)} @ {formatted_installed_agents}")
            else:
                for item in items:
                    if short:
                        displayed_items.append((item.image_ref.canonical, item.config_digest))
                    else:
                        print(_describe(item))
            if short:
                print(tabulate(displayed_items, tablefmt="plain"))
        except Exception as e:
            log.exception(f"An error occurred. Error: {e}")


async def inspect_image(cli_ctx: CLIContext, canonical_or_alias: str, architecture: str) -> None:
    _register_image_cli_orm_cluster()
    bootstrap_config = await cli_ctx.get_bootstrap_config()
    async with connect_database(bootstrap_config.db) as db:
        try:
            image = await _first_image(
                db, _reference_searcher(canonical_or_alias, architecture), canonical_or_alias
            )
            async with db.begin_readonly_session() as session:
                image_row = await session.get_one(
                    ImageRow, image.id, options=[selectinload(ImageRow.aliases)]
                )
                pprint(await image_row.inspect())
        except UnknownImageReference:
            log.exception("Image not found.")
        except Exception as e:
            log.exception(f"An error occurred. Error: {e}")


async def forget_image(cli_ctx: CLIContext, canonical_or_alias: str, architecture: str) -> None:
    _register_image_cli_orm_cluster()
    bootstrap_config = await cli_ctx.get_bootstrap_config()
    async with connect_database(bootstrap_config.db) as db:
        try:
            image = await _first_image(
                db, _reference_searcher(canonical_or_alias, architecture), canonical_or_alias
            )
            async with db.begin_session() as session:
                image_row = await session.get_one(ImageRow, image.id)
                await image_row.mark_as_deleted(session)
        except UnknownImageReference:
            log.exception("Image not found.")
        except Exception as e:
            log.exception(f"An error occurred. Error: {e}")


async def purge_image(
    cli_ctx: CLIContext, canonical_or_alias: str, architecture: str, remove_from_registry: bool
) -> None:
    _register_image_cli_orm_cluster()
    bootstrap_config = await cli_ctx.get_bootstrap_config()
    async with (
        connect_database(bootstrap_config.db) as db,
        db.begin_session() as session,
    ):
        try:
            image = await _first_image(
                db, _reference_searcher(canonical_or_alias, architecture), canonical_or_alias
            )
            async with V2DBOpsProvider(db).write_ops() as w:
                await w.purge_entity(ImagePurger(image_id=image.id))

            if remove_from_registry:
                registry_info = await session.get(ContainerRegistryRow, image.registry_id)
                if registry_info is None:
                    raise click.ClickException(f"Registry not found for image {image.name}")
                if registry_info.type != ContainerRegistryType.HARBOR2:
                    raise click.ClickException(
                        "Untagging from the registry is only supported for Harbor v2 registries"
                    )
                scanner = HarborRegistry_v2(db, image.image_ref.registry, registry_info)
                await scanner.untag(image.image_ref)

        except UnknownImageReference:
            log.exception("Image not found.")
        except Exception as e:
            log.exception(f"An error occurred. Error: {e}")


async def set_image_resource_limit(
    cli_ctx: CLIContext,
    canonical_or_alias: str,
    slot_type: str,
    range_value: tuple[Decimal | None, Decimal | None],
    architecture: str,
) -> None:
    _register_image_cli_orm_cluster()
    bootstrap_config = await cli_ctx.get_bootstrap_config()
    async with connect_database(bootstrap_config.db) as db:
        try:
            image = await _first_image(
                db, _reference_searcher(canonical_or_alias, architecture), canonical_or_alias
            )
            async with db.begin_session() as session:
                image_row = await session.get_one(ImageRow, image.id)
                image_row.set_resource_limit(slot_type, range_value)
        except UnknownImageReference:
            log.exception("Image not found.")
        except Exception as e:
            log.exception(f"An error occurred. Error: {e}")


async def rescan_images(
    cli_ctx: CLIContext, registry_or_image: str, project: str | None = None
) -> None:
    if not registry_or_image:
        raise click.BadArgumentUsage("Please specify a valid registry or full image name.")
    _register_image_cli_orm_cluster()
    bootstrap_config = await cli_ctx.get_bootstrap_config()
    async with (
        connect_database(bootstrap_config.db) as db,
    ):
        try:
            result = await ImageDBSource(db, V2DBOpsProvider(db)).rescan_images(
                registry_or_image, project
            )
            for error in result.errors:
                log.error(f"Failed to scan registries: {error}")
        except Exception as e:
            log.exception(f"Unknown error occurred. Error: {e}")


async def alias(cli_ctx: CLIContext, alias: str, target: str, architecture: str) -> None:
    _register_image_cli_orm_cluster()
    bootstrap_config = await cli_ctx.get_bootstrap_config()
    async with connect_database(bootstrap_config.db) as db:
        try:
            image = await _first_image(db, _canonical_searcher(target, architecture), target)
            async with db.begin_session() as session:
                image_row = await session.get_one(ImageRow, image.id)
                await ImageAliasRow.create(session, alias, image_row)
        except UnknownImageReference:
            log.exception("Image not found.")
        except Exception as e:
            log.exception(f"An error occurred. Error: {e}")


async def dealias(cli_ctx: CLIContext, alias: str) -> None:
    _register_image_cli_orm_cluster()
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
    _register_image_cli_orm_cluster()
    bootstrap_config = await cli_ctx.get_bootstrap_config()
    async with connect_database(bootstrap_config.db) as db:
        try:
            image = await _first_image(
                db,
                AliasedImageSearcher(alias, [ImageStatus.ALIVE]),
                alias,
            )
            for key, value in validate_image_labels(image.labels.label_data).items():
                print(f"{key:<40}: {value}")

        except UnknownImageReference:
            log.error(f"No images were found with alias: {alias}")
        except Exception as e:
            log.exception(f"An error occurred. Error: {e}")


def _resolve_architecture(current: bool, architecture: str | None) -> str:
    if architecture is not None:
        return architecture
    if current:
        return CURRENT_ARCH

    raise ValueError("Unreachable code!")


async def validate_image_canonical(
    cli_ctx: CLIContext, canonical: str, current: bool, architecture: str | None = None
) -> None:
    _register_image_cli_orm_cluster()
    bootstrap_config = await cli_ctx.get_bootstrap_config()
    async with (
        connect_database(bootstrap_config.db) as db,
        db.begin_readonly_session() as session,
    ):
        try:
            if current or architecture is not None:
                resolved_arch = _resolve_architecture(current, architecture)
                image = await _first_image(
                    db, _canonical_searcher(canonical, resolved_arch), canonical
                )

                print(f"{'architecture':<40}: {resolved_arch}")
                for key, value in validate_image_labels(image.labels.label_data).items():
                    print(f"{key:<40}: {value}")
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
                        print(f"{key:<40}: {value}")

        except UnknownImageReference as e:
            log.error(f"{e}")
        except Exception as e:
            log.exception(f"An error occurred. Error: {e}")
