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
from ai.backend.common.dto.manager.v2.entity_invitation.types import (
    EntityInvitationSideDTO,
    EntityInvitationStatusDTO,
)
from ai.backend.common.dto.manager.v2.rbac.types import PermissionBitDTO


@click.group()
def entity_invitation() -> None:
    """Entity invitation commands."""


def _parse_sides(sides: tuple[str, ...]) -> list[tuple[EntityInvitationSideDTO, str | None]]:
    """Read each ``--side`` value: a bare side, or ``target:<type>:<id>``."""
    parsed: list[tuple[EntityInvitationSideDTO, str | None]] = []
    for raw in sides:
        side_raw, sep, rest = raw.partition(":")
        try:
            side = EntityInvitationSideDTO(side_raw)
        except ValueError:
            valid = ", ".join(member.value for member in EntityInvitationSideDTO)
            raise click.BadParameter(
                f"Unknown side {side_raw!r}; expected one of: {valid}.",
                param_hint="--side",
            ) from None
        if side is EntityInvitationSideDTO.TARGET:
            if not sep or rest.count(":") != 1:
                raise click.BadParameter(
                    f"Invalid side item {raw!r}; expected 'target:<entity_type>:<entity_id>'.",
                    param_hint="--side",
                )
        elif sep:
            raise click.BadParameter(
                f"Side {side.value!r} names no entity, but {raw!r} does.",
                param_hint="--side",
            )
        parsed.append((side, rest or None))
    return parsed


@entity_invitation.command()
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
    from ai.backend.common.dto.manager.v2.entity_invitation.request import (
        CreateEntityInvitationInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.entity_invitation.create(
                CreateEntityInvitationInput(
                    target_entity_type=EntityType(entity_type),
                    target_entity_id=entity_id,
                    invitee_email=email,
                    permissions=[PermissionBitDTO(p) for p in permissions],
                )
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@entity_invitation.command()
@click.argument("invitation_id", type=click.UUID)
def get(invitation_id: uuid.UUID) -> None:
    """Read one invitation from the side that offered it."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            print_result(await registry.entity_invitation.get(invitation_id))
        finally:
            await registry.close()

    asyncio.run(_run())


@entity_invitation.command()
@click.argument("invitation_id", type=click.UUID)
def accept(invitation_id: uuid.UUID) -> None:
    """Take what was offered."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            print_result(await registry.entity_invitation.accept(invitation_id))
        finally:
            await registry.close()

    asyncio.run(_run())


@entity_invitation.command()
@click.argument("invitation_id", type=click.UUID)
def reject(invitation_id: uuid.UUID) -> None:
    """Turn down what was offered."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            print_result(await registry.entity_invitation.reject(invitation_id))
        finally:
            await registry.close()

    asyncio.run(_run())


@entity_invitation.command()
@click.argument("invitation_id", type=click.UUID)
def cancel(invitation_id: uuid.UUID) -> None:
    """Withdraw the offer before it was answered."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            print_result(await registry.entity_invitation.cancel(invitation_id))
        finally:
            await registry.close()

    asyncio.run(_run())


@entity_invitation.command(name="scoped-search")
@click.option(
    "--side",
    "sides",
    multiple=True,
    required=True,
    help=(
        "Side to read from (repeatable; OR across items): 'received', 'sent', or "
        "'target:<entity_type>:<entity_id>'."
    ),
)
@click.option(
    "--status",
    type=click.Choice([member.value for member in EntityInvitationStatusDTO]),
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
    sides: tuple[str, ...],
    status: str | None,
    limit: int,
    offset: int,
    order_by: tuple[str, ...],
) -> None:
    """Search the invitations the named sides reach."""
    from ai.backend.common.dto.manager.v2.entity_invitation.request import (
        EntityInvitationFilter,
        EntityInvitationOrderBy,
        EntityInvitationScopeDTO,
        EntityInvitationScopeItemDTO,
        EntityInvitationStatusFilter,
        ScopedSearchEntityInvitationsInput,
    )
    from ai.backend.common.dto.manager.v2.entity_invitation.types import (
        EntityInvitationOrderField,
    )

    items: list[EntityInvitationScopeItemDTO] = []
    for side, target in _parse_sides(sides):
        if target is None:
            items.append(EntityInvitationScopeItemDTO(side=side))
            continue
        entity_type, _, entity_id = target.partition(":")
        try:
            target_id = uuid.UUID(entity_id)
        except ValueError:
            raise click.BadParameter(
                f"Entity identifier {entity_id!r} must be a UUID.",
                param_hint="--side",
            ) from None
        items.append(
            EntityInvitationScopeItemDTO(
                side=side,
                target_entity_type=EntityType(entity_type),
                target_entity_id=target_id,
            )
        )

    filter_dto = (
        EntityInvitationFilter(
            status=EntityInvitationStatusFilter(equals=EntityInvitationStatusDTO(status))
        )
        if status is not None
        else None
    )
    orders = (
        parse_order_options(order_by, EntityInvitationOrderField, EntityInvitationOrderBy)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.entity_invitation.scoped_search(
                ScopedSearchEntityInvitationsInput(
                    scope=EntityInvitationScopeDTO(items=items),
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
