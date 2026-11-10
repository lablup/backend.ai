"""CLI commands for resource slot type management."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)


@click.group(name="slot-type")
def slot_type() -> None:
    """Resource slot type commands."""


@slot_type.command()
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option(
    "--slot-name",
    default=None,
    type=str,
    help="Filter slot types whose slot name contains this substring.",
)
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., slot_name:asc, rank:desc).",
)
def search(
    limit: int | None,
    offset: int | None,
    slot_name: str | None,
    order_by: tuple[str, ...],
) -> None:
    """Search resource slot types."""
    from ai.backend.common.dto.manager.v2.resource_slot.request import (
        AdminSearchResourceSlotTypesInput,
        ResourceSlotTypeFilter,
        ResourceSlotTypeOrder,
    )
    from ai.backend.common.dto.manager.v2.resource_slot.types import ResourceSlotTypeOrderField

    # Build filter only if any filter option is provided
    filter_dto: ResourceSlotTypeFilter | None = None
    if slot_name is not None:
        from ai.backend.common.dto.manager.query import StringFilter

        filter_dto = ResourceSlotTypeFilter(
            slot_name=StringFilter(contains=slot_name),
        )

    # Build order only if --order-by is provided
    orders = (
        parse_order_options(order_by, ResourceSlotTypeOrderField, ResourceSlotTypeOrder)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_slot.search_slot_types(
                AdminSearchResourceSlotTypesInput(
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


@slot_type.command()
@click.argument("slot_name", type=str)
@click.argument(
    "slot_type_category",
    type=click.Choice(["count", "bytes", "unique", "unified"]),
)
@click.option("--required/--not-required", default=False, help="Whether requests must name it.")
@click.option("--enabled/--disabled", default=True, help="Whether the scheduler considers it.")
@click.option("--display-name", default="", help="Human-readable name.")
@click.option("--description", default="", help="Longer description.")
@click.option("--display-unit", default="", help="Unit label (e.g., GiB).")
@click.option("--display-icon", default="", help="Icon identifier for UIs.")
@click.option("--binary/--decimal", default=False, help="Binary (1024) or decimal (1000) prefixes.")
@click.option("--round-length", type=int, default=0, help="Decimal places when displaying.")
@click.option("--rank", type=int, default=0, help="Display ordering rank.")
def create(
    slot_name: str,
    slot_type_category: str,
    required: bool,
    enabled: bool,
    display_name: str,
    description: str,
    display_unit: str,
    display_icon: str,
    binary: bool,
    round_length: int,
    rank: int,
) -> None:
    """Register a new resource slot type."""
    from ai.backend.common.dto.manager.v2.resource_slot.request import (
        CreateResourceSlotTypeInput,
    )
    from ai.backend.common.dto.manager.v2.resource_slot.types import NumberFormatInput

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_slot.admin_create_slot_type(
                CreateResourceSlotTypeInput(
                    slot_name=slot_name,
                    slot_type=slot_type_category,
                    required=required,
                    enabled=enabled,
                    display_name=display_name,
                    description=description,
                    display_unit=display_unit,
                    display_icon=display_icon,
                    number_format=NumberFormatInput(binary=binary, round_length=round_length),
                    rank=rank,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@slot_type.command()
@click.argument("slot_name", type=str)
@click.option(
    "--required/--not-required", "required", default=None, help="Whether requests must name it."
)
@click.option(
    "--enabled/--disabled", "enabled", default=None, help="Whether the scheduler considers it."
)
@click.option("--display-name", default=None, help="Human-readable name.")
@click.option("--description", default=None, help="Longer description.")
@click.option("--display-unit", default=None, help="Unit label (e.g., GiB).")
@click.option("--display-icon", default=None, help="Icon identifier for UIs.")
@click.option(
    "--binary/--decimal",
    "binary",
    default=None,
    help="Binary (1024) or decimal (1000) prefixes. Sets the number format.",
)
@click.option(
    "--round-length",
    type=int,
    default=None,
    help="Decimal places when displaying. Sets the number format.",
)
@click.option("--rank", type=int, default=None, help="Display ordering rank.")
def update(
    slot_name: str,
    required: bool | None,
    enabled: bool | None,
    display_name: str | None,
    description: str | None,
    display_unit: str | None,
    display_icon: str | None,
    binary: bool | None,
    round_length: int | None,
    rank: int | None,
) -> None:
    """Update a resource slot type. The slot name and slot type are immutable."""
    from ai.backend.common.dto.manager.v2.resource_slot.request import (
        UpdateResourceSlotTypeInput,
    )
    from ai.backend.common.dto.manager.v2.resource_slot.types import NumberFormatInput

    # The server replaces the whole number_format object, so both parts are sent
    # together; the unset one falls back to the DTO default.
    number_format = (
        NumberFormatInput(
            binary=binary if binary is not None else False,
            round_length=round_length if round_length is not None else 0,
        )
        if binary is not None or round_length is not None
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_slot.admin_update_slot_type(
                slot_name,
                UpdateResourceSlotTypeInput(
                    slot_name=slot_name,
                    required=required,
                    enabled=enabled,
                    display_name=display_name,
                    description=description,
                    display_unit=display_unit,
                    display_icon=display_icon,
                    number_format=number_format,
                    rank=rank,
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@slot_type.command()
@click.argument("slot_name", type=str)
def delete(slot_name: str) -> None:
    """Remove a resource slot type. Refused while anything still references it."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.resource_slot.admin_purge_slot_type(slot_name)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
