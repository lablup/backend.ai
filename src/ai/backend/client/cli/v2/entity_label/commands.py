"""CLI commands for entity labels."""

from __future__ import annotations

import asyncio
import uuid

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)


@click.group(name="entity-label")
def entity_label() -> None:
    """Entity label commands."""


@entity_label.command()
@click.option("--entity-type", required=True, type=str, help="Type of the entity to label.")
@click.option("--entity-id", required=True, type=click.UUID, help="ID of the entity to label.")
@click.option("--key", required=True, type=str, help="Label key.")
@click.option("--value", required=True, type=str, help="Label value.")
def upsert(entity_type: str, entity_id: uuid.UUID, key: str, value: str) -> None:
    """Set one key on an entity, replacing the value it carries."""
    from ai.backend.common.dto.manager.v2.entity.types import EntityTarget
    from ai.backend.common.dto.manager.v2.entity_label.request import UpsertEntityLabelInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.entity_label.upsert(
                UpsertEntityLabelInput(
                    target=EntityTarget(entity_type=entity_type, entity_id=entity_id),
                    key=key,
                    value=value,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@entity_label.command(name="bulk-upsert")
@click.option("--entity-type", required=True, type=str, help="Type of the entities to label.")
@click.option(
    "--entity-id",
    required=True,
    multiple=True,
    type=click.UUID,
    help="ID of an entity to label. Repeat to name several.",
)
@click.option(
    "--label",
    "labels",
    required=True,
    multiple=True,
    type=str,
    help="A KEY=VALUE label to put on every entity named. Repeat to put several.",
)
def bulk_upsert(
    entity_type: str, entity_id: tuple[uuid.UUID, ...], labels: tuple[str, ...]
) -> None:
    """Put every label named on every entity named, answering per entity."""
    from ai.backend.common.dto.manager.v2.entity.types import EntityTarget
    from ai.backend.common.dto.manager.v2.entity_label.request import (
        PartialBulkUpsertEntityLabelInput,
        UpsertEntityLabelInput,
    )

    pairs: list[tuple[str, str]] = []
    for label in labels:
        key, sep, value = label.partition("=")
        if not sep or not key or not value:
            raise click.BadParameter(f"{label!r} is not KEY=VALUE", param_hint="--label")
        pairs.append((key, value))

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.entity_label.partial_bulk_upsert(
                PartialBulkUpsertEntityLabelInput(
                    items=[
                        UpsertEntityLabelInput(
                            target=EntityTarget(entity_type=entity_type, entity_id=one_id),
                            key=key,
                            value=value,
                        )
                        for one_id in entity_id
                        for key, value in pairs
                    ],
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@entity_label.command()
@click.argument("label_id", type=click.UUID)
def purge(label_id: uuid.UUID) -> None:
    """Take one label off, named by its own ID."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.entity_label.purge(label_id)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@entity_label.command(name="bulk-purge")
@click.argument("label_ids", nargs=-1, required=True, type=click.UUID)
def bulk_purge(label_ids: tuple[uuid.UUID, ...]) -> None:
    """Take several labels off by ID, answering per label."""
    from ai.backend.common.dto.manager.v2.entity_label.request import (
        PartialBulkPurgeEntityLabelInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.entity_label.partial_bulk_purge(
                PartialBulkPurgeEntityLabelInput(ids=list(label_ids)),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@entity_label.command()
@click.option("--entity-type", required=True, type=str, help="Type of the entity to read.")
@click.option(
    "--entity-id",
    required=True,
    multiple=True,
    type=click.UUID,
    help="ID of an entity to read the labels of. Repeat to name several.",
)
@click.option("--key", type=str, default=None, help="Filter by label key (exact match).")
@click.option("--value", type=str, default=None, help="Filter by label value (exact match).")
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., created_at:desc). Fields: key, value, created_at.",
)
def search(
    entity_type: str,
    entity_id: tuple[uuid.UUID, ...],
    key: str | None,
    value: str | None,
    limit: int | None,
    offset: int | None,
    order_by: tuple[str, ...],
) -> None:
    """Read the labels on the entities named."""
    from ai.backend.common.dto.manager.query import StringFilter
    from ai.backend.common.dto.manager.v2.entity.types import EntityTarget
    from ai.backend.common.dto.manager.v2.entity_label.request import (
        EntityLabelFilter,
        EntityLabelOrder,
        SearchEntityLabelsInput,
    )
    from ai.backend.common.dto.manager.v2.entity_label.types import EntityLabelOrderField

    filter_dto: EntityLabelFilter | None = None
    if key is not None or value is not None:
        filter_dto = EntityLabelFilter(
            key=StringFilter(equals=key) if key is not None else None,
            value=StringFilter(equals=value) if value is not None else None,
        )

    orders = (
        parse_order_options(order_by, EntityLabelOrderField, EntityLabelOrder) if order_by else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.entity_label.search(
                SearchEntityLabelsInput(
                    scope=[
                        EntityTarget(entity_type=entity_type, entity_id=one_id)
                        for one_id in entity_id
                    ],
                    filter=filter_dto,
                    order=orders,
                    limit=limit,
                    offset=offset,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
