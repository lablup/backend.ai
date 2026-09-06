"""User-facing CLI commands for entity invitations."""

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
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.dto.manager.v2.entity_share.types import EntityShareStatusDTO
from ai.backend.common.dto.manager.v2.rbac.types import PermissionBitDTO


@click.group()
def entity_share() -> None:
    """Entity invitation commands."""


def _parse_targets(targets: tuple[str, ...]) -> list[tuple[str, uuid.UUID]]:
    """Read each ``--target`` value, given as ``<entity_type>:<entity_id>``."""
    parsed: list[tuple[str, uuid.UUID]] = []
    for raw in targets:
        entity_type, sep, entity_id = raw.partition(":")
        if not sep or not entity_id:
            raise click.BadParameter(
                f"Invalid target {raw!r}; expected '<entity_type>:<entity_id>'.",
                param_hint="--target",
            )
        try:
            parsed.append((entity_type, uuid.UUID(entity_id)))
        except ValueError:
            raise click.BadParameter(
                f"Entity identifier {entity_id!r} must be a UUID.",
                param_hint="--target",
            ) from None
    return parsed


@entity_share.command()
@click.option("--entity-type", required=True, help="Type of the entity being offered.")
@click.option("--entity-id", type=click.UUID, required=True, help="Id of the entity being offered.")
@click.option("--email", required=True, help="Address the offer goes to.")
@click.option(
    "--permission",
    "permissions",
    multiple=True,
    type=click.Choice([member.value for member in PermissionBitDTO]),
    help="Permission the offer caps at (repeatable); omit for no ceiling.",
)
def create(
    entity_type: str, entity_id: uuid.UUID, email: str, permissions: tuple[str, ...]
) -> None:
    """Offer one entity to one address."""
    from ai.backend.common.dto.manager.v2.entity_share.request import (
        CreateEntityShareInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.entity_share.create(
                CreateEntityShareInput(
                    target_entity_type=EntityType(entity_type),
                    target_entity_id=entity_id,
                    recipient_email=email,
                    permissions=[PermissionBitDTO(p) for p in permissions],
                )
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@entity_share.command()
@click.argument("share_id", type=click.UUID)
def get(share_id: uuid.UUID) -> None:
    """Read one invitation from the side that offered it."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            print_result(await registry.entity_share.get(share_id))
        finally:
            await registry.close()

    asyncio.run(_run())


@entity_share.command()
@click.argument("share_id", type=click.UUID)
def accept(share_id: uuid.UUID) -> None:
    """Take what was offered."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            print_result(await registry.entity_share.accept(share_id))
        finally:
            await registry.close()

    asyncio.run(_run())


@entity_share.command()
@click.argument("share_id", type=click.UUID)
def reject(share_id: uuid.UUID) -> None:
    """Turn down what was offered."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            print_result(await registry.entity_share.reject(share_id))
        finally:
            await registry.close()

    asyncio.run(_run())


@entity_share.command()
@click.argument("share_id", type=click.UUID)
def cancel(share_id: uuid.UUID) -> None:
    """Withdraw the offer before it was answered."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            print_result(await registry.entity_share.cancel(share_id))
        finally:
            await registry.close()

    asyncio.run(_run())


@entity_share.command(name="scoped-search")
@click.option(
    "--invitee",
    "invitees",
    multiple=True,
    type=click.UUID,
    help="User the invitations are addressed to (repeatable).",
)
@click.option(
    "--inviter",
    "inviters",
    multiple=True,
    type=click.UUID,
    help="User who sent the invitations (repeatable).",
)
@click.option(
    "--target",
    "targets",
    multiple=True,
    help="Entity the invitations offer, as '<entity_type>:<entity_id>' (repeatable).",
)
@click.option(
    "--status",
    type=click.Choice([member.value for member in EntityShareStatusDTO]),
    default=None,
    help="Filter by status.",
)
@click.option("--limit", type=int, default=20, help="Maximum number of items to return.")
@click.option("--offset", type=int, default=0, help="Number of items to skip.")
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., created_at:desc, status:asc).",
)
def scoped_search(
    invitees: tuple[uuid.UUID, ...],
    inviters: tuple[uuid.UUID, ...],
    targets: tuple[str, ...],
    status: str | None,
    limit: int,
    offset: int,
    order_by: tuple[str, ...],
) -> None:
    """Search the invitations the named scopes reach (OR across all of them)."""
    from ai.backend.common.dto.manager.v2.entity_share.request import (
        EntityShareFilter,
        EntityShareOrderBy,
        EntityShareScope,
        EntityShareStatusFilter,
        EntityShareTargetScope,
        ScopedSearchEntitySharesInput,
    )
    from ai.backend.common.dto.manager.v2.entity_share.types import (
        EntityShareOrderField,
    )
    from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope

    if not invitees and not inviters and not targets:
        raise click.UsageError("Name at least one of --invitee, --inviter or --target.")

    scope = EntityShareScope(
        invitee=[UUIDScope(value=user_id) for user_id in invitees] or None,
        inviter=[UUIDScope(value=user_id) for user_id in inviters] or None,
        target=[
            EntityShareTargetScope(entity_type=EntityType(entity_type), entity_id=entity_id)
            for entity_type, entity_id in _parse_targets(targets)
        ]
        or None,
    )
    filter_dto = (
        EntityShareFilter(status=EntityShareStatusFilter(equals=EntityShareStatusDTO(status)))
        if status is not None
        else None
    )
    orders = (
        parse_order_options(order_by, EntityShareOrderField, EntityShareOrderBy)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.entity_share.scoped_search(
                ScopedSearchEntitySharesInput(
                    scope=scope,
                    filter=filter_dto,
                    order=orders,
                    limit=limit,
                    offset=offset,
                )
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
