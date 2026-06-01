"""CLI commands for RBAC role invitation management."""

from __future__ import annotations

import asyncio
from uuid import UUID

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    print_result,
)


@click.group()
def invitation() -> None:
    """Role invitation commands."""


@invitation.command()
@click.option("--role-id", type=click.UUID, required=True, help="Role ID to invite for.")
@click.option(
    "--email",
    multiple=True,
    required=True,
    help="Invitee email address (repeatable).",
)
def create(role_id: UUID, email: tuple[str, ...]) -> None:
    """Create role invitations by email."""
    from ai.backend.common.dto.manager.v2.role_invitation.request import (
        CreateRoleInvitationInput,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.role_invitation.create(
                CreateRoleInvitationInput(
                    role_id=role_id,
                    emails=list(email),
                ),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@invitation.command()
@click.argument("invitation_id", type=click.UUID)
def accept(invitation_id: UUID) -> None:
    """Accept a pending invitation."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.role_invitation.accept(invitation_id)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@invitation.command()
@click.argument("invitation_id", type=click.UUID)
def reject(invitation_id: UUID) -> None:
    """Reject a pending invitation."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.role_invitation.reject(invitation_id)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@invitation.command()
@click.argument("invitation_id", type=click.UUID)
def cancel(invitation_id: UUID) -> None:
    """Cancel a pending invitation."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.role_invitation.cancel(invitation_id)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@invitation.command(name="my-search")
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., created_at:desc, state:asc).",
)
def my_search(limit: int | None, offset: int | None, order_by: tuple[str, ...]) -> None:
    """Search your own invitations."""
    from ai.backend.client.cli.v2.helpers import parse_order_options
    from ai.backend.common.dto.manager.v2.role_invitation.request import (
        RoleInvitationOrderBy,
        RoleInvitationOrderField,
        SearchRoleInvitationsInput,
    )

    orders = (
        parse_order_options(order_by, RoleInvitationOrderField, RoleInvitationOrderBy)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.role_invitation.my_search(
                SearchRoleInvitationsInput(order=orders, limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@invitation.command(name="my-sent-search")
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., created_at:desc, state:asc).",
)
def my_sent_search(limit: int | None, offset: int | None, order_by: tuple[str, ...]) -> None:
    """Search invitations you have sent."""
    from ai.backend.client.cli.v2.helpers import parse_order_options
    from ai.backend.common.dto.manager.v2.role_invitation.request import (
        RoleInvitationOrderBy,
        RoleInvitationOrderField,
        SearchRoleInvitationsInput,
    )

    orders = (
        parse_order_options(order_by, RoleInvitationOrderField, RoleInvitationOrderBy)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.role_invitation.my_sent_search(
                SearchRoleInvitationsInput(order=orders, limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@invitation.command(name="role-search")
@click.argument("role_id", type=click.UUID)
@click.option("--limit", type=int, default=None, help="Maximum items to return.")
@click.option("--offset", type=int, default=None, help="Number of items to skip.")
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., created_at:desc, state:asc).",
)
def role_search(
    role_id: UUID, limit: int | None, offset: int | None, order_by: tuple[str, ...]
) -> None:
    """Search invitations for a specific role (admin view)."""
    from ai.backend.client.cli.v2.helpers import parse_order_options
    from ai.backend.common.dto.manager.v2.role_invitation.request import (
        RoleInvitationOrderBy,
        RoleInvitationOrderField,
        SearchRoleInvitationsInput,
    )

    orders = (
        parse_order_options(order_by, RoleInvitationOrderField, RoleInvitationOrderBy)
        if order_by
        else None
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.role_invitation.search_by_role(
                role_id,
                SearchRoleInvitationsInput(order=orders, limit=limit, offset=offset),
            )
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
