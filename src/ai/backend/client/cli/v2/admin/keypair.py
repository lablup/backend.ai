"""Admin CLI commands for the v2 keypair resource."""

from __future__ import annotations

import asyncio

import click

from ai.backend.client.cli.v2.helpers import (
    create_v2_registry,
    load_v2_config,
    parse_order_options,
    print_result,
)


@click.group()
def keypair() -> None:
    """Admin keypair commands."""


@keypair.command()
@click.option("--limit", default=20, help="Maximum number of results to return.")
@click.option("--offset", default=0, help="Number of results to skip.")
@click.option(
    "--is-active/--no-is-active",
    default=None,
    help="Filter by active status.",
)
@click.option(
    "--is-admin/--no-is-admin",
    default=None,
    help="Filter by admin flag.",
)
@click.option(
    "--order-by",
    multiple=True,
    help="Order by field:direction (e.g., created_at:desc, access_key:asc).",
)
def search(
    limit: int,
    offset: int,
    is_active: bool | None,
    is_admin: bool | None,
    order_by: tuple[str, ...],
) -> None:
    """Search all keypairs (superadmin only)."""
    from ai.backend.common.dto.manager.v2.keypair.request import (
        AdminSearchKeypairsInput,
        KeypairFilter,
        KeypairOrderBy,
    )
    from ai.backend.common.dto.manager.v2.keypair.types import KeypairOrderField

    filter_dto: KeypairFilter | None = None
    if is_active is not None or is_admin is not None:
        filter_dto = KeypairFilter(
            is_active=is_active,
            is_admin=is_admin,
        )

    orders = parse_order_options(order_by, KeypairOrderField, KeypairOrderBy) if order_by else None

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.keypair.admin_search(
                AdminSearchKeypairsInput(
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


@keypair.command()
@click.argument("access_key")
def get(access_key: str) -> None:
    """Get a keypair by access key (superadmin only)."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.keypair.admin_get(access_key)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@keypair.command()
@click.argument("body", type=str)
def create(body: str) -> None:
    """Create a keypair for a user (superadmin only).

    BODY is a JSON string with keypair creation fields.
    Example: '{"user_id": "...", "resource_policy": "default"}'
    """
    import json
    import sys

    from ai.backend.common.dto.manager.v2.keypair.request import AdminCreateKeypairInput

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON: {e}", err=True)
        sys.exit(1)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.keypair.admin_create(AdminCreateKeypairInput(**data))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@keypair.command()
@click.argument("body", type=str)
def update(body: str) -> None:
    """Update a keypair (superadmin only).

    BODY is a JSON string with update fields. Must include 'access_key'.
    Example: '{"access_key": "AKIAIOSFODNN7EXAMPLE", "is_active": false}'
    """
    import json
    import sys

    from ai.backend.common.dto.manager.v2.keypair.request import AdminUpdateKeypairInput

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON: {e}", err=True)
        sys.exit(1)

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.keypair.admin_update(AdminUpdateKeypairInput(**data))
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@keypair.command()
@click.argument("access_key")
def delete(access_key: str) -> None:
    """Delete a keypair (superadmin only)."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.keypair.admin_delete(access_key)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@keypair.group(name="ssh")
def ssh() -> None:
    """Admin SSH keypair commands (register/get/delete a user's SSH keypair)."""


@ssh.command(name="register")
@click.option("--access-key", required=True, type=str, help="Target access key.")
@click.option(
    "--public-key-file",
    required=True,
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help="Path to PEM-encoded SSH public key file.",
)
@click.option(
    "--private-key-file",
    required=True,
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help="Path to PEM-encoded SSH private key file.",
)
def ssh_register(access_key: str, public_key_file: str, private_key_file: str) -> None:
    """Register (overwrite) a user's SSH keypair (superadmin only)."""
    from pathlib import Path

    from ai.backend.common.dto.manager.v2.keypair.request import AdminRegisterSSHKeypairInput

    ssh_public_key = Path(public_key_file).read_text(encoding="utf-8")
    ssh_private_key = Path(private_key_file).read_text(encoding="utf-8")
    input_dto = AdminRegisterSSHKeypairInput(
        access_key=access_key,
        ssh_public_key=ssh_public_key,
        ssh_private_key=ssh_private_key,
    )

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.keypair.admin_register_ssh_keypair(input_dto)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@ssh.command(name="get")
@click.argument("access_key")
def ssh_get(access_key: str) -> None:
    """Get a user's SSH public key (superadmin only)."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.keypair.admin_get_ssh_keypair(access_key)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())


@ssh.command(name="delete")
@click.argument("access_key")
def ssh_delete(access_key: str) -> None:
    """Clear a user's SSH keypair (superadmin only)."""

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.keypair.admin_delete_ssh_keypair(access_key)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
